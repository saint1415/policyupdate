"""
Flask Web Application
Web interface for the GRC Policy Management Platform
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
WEB_DIR = Path(__file__).parent
PROJECT_ROOT = WEB_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from flask import Flask, render_template, request, jsonify, send_file
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from core.config import get_config, setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger('web')


def create_app(config=None):
    """Create and configure the Flask application"""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask not installed. Run: pip install flask")

    app_config = get_config()

    app = Flask(__name__,
                template_folder=str(PROJECT_ROOT / "src" / "web" / "templates"),
                static_folder=str(PROJECT_ROOT / "src" / "web" / "static"))

    # Use secure secret key from config (not hardcoded)
    app.config['SECRET_KEY'] = app_config.web.secret_key
    app.config['PROJECT_ROOT'] = PROJECT_ROOT

    if config:
        app.config.update(config)

    logger.info("Flask application initialized")

    # Lazy-load modules
    _cache = {}

    def get_package_builder():
        if 'builder' not in _cache:
            from generation.package_builder import PackageBuilder
            _cache['builder'] = PackageBuilder(
                str(PROJECT_ROOT / "policies"),
                str(PROJECT_ROOT / "config" / "frameworks")
            )
        return _cache['builder']

    def get_compliance_mapper():
        if 'mapper' not in _cache:
            from core.compliance_mapper import ComplianceMapper
            mapper = ComplianceMapper()
            mapper.load_all_frameworks(str(PROJECT_ROOT / "config" / "frameworks"))
            _cache['mapper'] = mapper
        return _cache['mapper']

    def get_gap_analyzer():
        if 'analyzer' not in _cache:
            from core.gap_analyzer import GapAnalyzer
            analyzer = GapAnalyzer(compliance_mapper=get_compliance_mapper())
            analyzer.load_policy_library_from_dir(str(PROJECT_ROOT / "policies"))
            _cache['analyzer'] = analyzer
        return _cache['analyzer']

    def get_client_manager():
        if 'clients' not in _cache:
            from crm.client_manager import ClientManager
            _cache['clients'] = ClientManager(str(PROJECT_ROOT / "data" / "clients.db"))
        return _cache['clients']

    def get_feed_monitor():
        if 'monitor' not in _cache:
            from automation.feed_monitor import FeedMonitor
            _cache['monitor'] = FeedMonitor(str(PROJECT_ROOT / "data" / "feeds.db"))
        return _cache['monitor']

    # =========================================================================
    # ROUTES
    # =========================================================================

    @app.route('/')
    def index():
        """Dashboard home page"""
        mapper = get_compliance_mapper()
        builder = get_package_builder()
        manager = get_client_manager()

        # Get summary stats
        frameworks = list(mapper.frameworks.keys())
        policies = builder.get_all_policies()
        clients = manager.list_clients()

        total_controls = sum(fw.total_controls for fw in mapper.frameworks.values())

        return render_template('index.html',
            framework_count=len(frameworks),
            policy_count=len(policies),
            client_count=len(clients),
            control_count=total_controls
        )

    # -------------------------------------------------------------------------
    # POLICIES API
    # -------------------------------------------------------------------------

    @app.route('/api/policies')
    def api_policies():
        """Get all policies"""
        builder = get_package_builder()
        policies = builder.get_all_policies()

        result = []
        for pid, policy in policies.items():
            result.append({
                'id': policy.get('id', pid),
                'title': policy.get('title', ''),
                'category': policy.get('category', ''),
                'frameworks': list(policy.get('frameworks', {}).keys())
            })

        return jsonify(sorted(result, key=lambda x: (x['category'], x['title'])))

    @app.route('/api/policies/<policy_id>')
    def api_policy_detail(policy_id):
        """Get a single policy"""
        builder = get_package_builder()
        policies = builder.get_all_policies()

        if policy_id not in policies:
            return jsonify({'error': 'Policy not found'}), 404

        policy = policies[policy_id]
        return jsonify({
            'id': policy.get('id', policy_id),
            'title': policy.get('title', ''),
            'category': policy.get('category', ''),
            'frameworks': policy.get('frameworks', {}),
            'references': policy.get('references', []),
            'variables': policy.get('variables', []),
            'content_preview': policy.get('body', '')[:500]
        })

    @app.route('/api/policies/search')
    def api_policy_search():
        """Search policies"""
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify([])

        builder = get_package_builder()
        policies = builder.get_all_policies()

        results = []
        for pid, policy in policies.items():
            if (query in pid.lower() or
                query in policy.get('title', '').lower() or
                query in policy.get('body', '').lower()):
                results.append({
                    'id': policy.get('id', pid),
                    'title': policy.get('title', ''),
                    'category': policy.get('category', '')
                })

        return jsonify(results[:50])

    # -------------------------------------------------------------------------
    # FRAMEWORKS API
    # -------------------------------------------------------------------------

    @app.route('/api/frameworks')
    def api_frameworks():
        """Get all frameworks"""
        mapper = get_compliance_mapper()

        result = []
        for fw_id, framework in mapper.frameworks.items():
            summary = mapper.get_framework_summary(fw_id)
            result.append({
                'id': fw_id,
                'name': framework.name,
                'version': framework.version,
                'controls': summary['total_controls'],
                'required_policies': summary['required_policies']
            })

        return jsonify(sorted(result, key=lambda x: x['name']))

    @app.route('/api/frameworks/<framework_id>')
    def api_framework_detail(framework_id):
        """Get framework details"""
        mapper = get_compliance_mapper()

        if framework_id not in mapper.frameworks:
            return jsonify({'error': 'Framework not found'}), 404

        framework = mapper.frameworks[framework_id]
        summary = mapper.get_framework_summary(framework_id)

        return jsonify({
            'id': framework_id,
            'name': framework.name,
            'version': framework.version,
            'controls': summary['total_controls'],
            'required_policies': summary['required_policies'],
            'recommended_policies': summary['recommended_policies'],
            'control_list': [
                {'id': c.id, 'name': c.name, 'category': c.parent_category}
                for c in list(framework.controls.values())[:100]
            ]
        })

    @app.route('/api/frameworks/<framework_id>/coverage')
    def api_framework_coverage(framework_id):
        """Get framework coverage analysis"""
        analyzer = get_gap_analyzer()

        try:
            report = analyzer.analyze_framework(framework_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

        return jsonify({
            'framework_id': framework_id,
            'framework_name': report.framework_name,
            'total_controls': report.total_controls,
            'fully_covered': report.fully_covered_controls,
            'partially_covered': report.partially_covered_controls,
            'not_covered': report.not_covered_controls,
            'coverage_percentage': round(report.overall_coverage * 100, 1),
            'missing_policies': report.missing_policy_list[:20]
        })

    # -------------------------------------------------------------------------
    # CLIENTS API
    # -------------------------------------------------------------------------

    @app.route('/api/clients')
    def api_clients():
        """Get all clients"""
        manager = get_client_manager()
        clients = manager.list_clients()

        return jsonify([{
            'id': c.id,
            'name': c.name,
            'industry': c.industry,
            'size_tier': c.size_tier,
            'frameworks': c.target_frameworks
        } for c in clients])

    @app.route('/api/clients', methods=['POST'])
    def api_create_client():
        """Create a new client"""
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name required'}), 400

        manager = get_client_manager()
        client = manager.create_client(
            data['name'],
            industry=data.get('industry', ''),
            size_tier=data.get('size_tier', 'medium'),
            target_frameworks=data.get('frameworks', [])
        )

        return jsonify({
            'id': client.id,
            'name': client.name,
            'message': 'Client created successfully'
        }), 201

    @app.route('/api/clients/<client_id>')
    def api_client_detail(client_id):
        """Get client details"""
        manager = get_client_manager()
        summary = manager.get_client_summary(client_id)

        if 'error' in summary:
            return jsonify({'error': 'Client not found'}), 404

        return jsonify(summary)

    @app.route('/api/clients/<client_id>', methods=['DELETE'])
    def api_delete_client(client_id):
        """Delete a client"""
        manager = get_client_manager()
        manager.delete_client(client_id)
        return jsonify({'message': 'Client deleted'})

    # -------------------------------------------------------------------------
    # GENERATION API
    # -------------------------------------------------------------------------

    @app.route('/api/generate', methods=['POST'])
    def api_generate():
        """Generate a policy package"""
        data = request.get_json()
        if not data or 'client_name' not in data:
            return jsonify({'error': 'client_name required'}), 400

        from generation.package_builder import ClientConfig

        builder = get_package_builder()

        # Build config
        variables = {
            'ORGANIZATION_NAME': data.get('org_name', data['client_name']),
            'CSO_TITLE': data.get('cso_title', 'Chief Security Officer'),
            'EXEC_MGMT': 'Executive Management',
            'IT_STAFF': 'IT Staff',
            'HR_DEPARTMENT': 'Human Resources',
            'LEGAL_DEPARTMENT': 'Legal Department',
            'RMO_TITLE': 'Risk Management Officer'
        }

        config = ClientConfig(
            name=data['client_name'],
            variables=variables,
            frameworks=data.get('frameworks', [])
        )

        result = builder.build_package(config)

        # Determine output format
        output_format = data.get('format', 'docx')
        output_dir = PROJECT_ROOT / "output"
        output_dir.mkdir(exist_ok=True)

        safe_name = data['client_name'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        response_data = {
            'client_name': data['client_name'],
            'total_policies': result.total_policies,
            'incomplete_count': result.incomplete_count,
            'frameworks': result.frameworks_covered,
            'files': []
        }

        if output_format in ['docx', 'all']:
            try:
                from generation.docx_exporter import DocxExporter
                exporter = DocxExporter()
                docx_path = output_dir / f"{safe_name}_{timestamp}.docx"
                exporter.export_package(result, str(docx_path))
                response_data['files'].append({
                    'format': 'docx',
                    'filename': docx_path.name,
                    'path': str(docx_path)
                })
            except ImportError:
                response_data['docx_error'] = 'python-docx not installed'

        if output_format in ['pdf', 'all']:
            try:
                from generation.pdf_exporter import PdfExporter
                exporter = PdfExporter()
                pdf_path = output_dir / f"{safe_name}_{timestamp}.pdf"
                exporter.export_package(result, str(pdf_path))
                response_data['files'].append({
                    'format': 'pdf',
                    'filename': pdf_path.name,
                    'path': str(pdf_path)
                })
            except ImportError:
                response_data['pdf_error'] = 'weasyprint not installed'

        return jsonify(response_data)

    @app.route('/api/download/<filename>')
    def api_download(filename):
        """Download a generated file"""
        output_dir = PROJECT_ROOT / "output"
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(str(file_path), as_attachment=True)

    # -------------------------------------------------------------------------
    # MONITORING API
    # -------------------------------------------------------------------------

    @app.route('/api/monitor/feeds')
    def api_monitor_feeds():
        """Get configured feeds"""
        monitor = get_feed_monitor()
        feeds = monitor.get_feeds(enabled_only=False)

        return jsonify([{
            'id': f.id,
            'name': f.name,
            'url': f.url,
            'type': f.feed_type,
            'keywords': f.keywords,
            'frameworks': f.frameworks,
            'enabled': f.enabled
        } for f in feeds])

    @app.route('/api/monitor/recent')
    def api_monitor_recent():
        """Get recent feed items"""
        days = request.args.get('days', 7, type=int)
        monitor = get_feed_monitor()
        items = monitor.get_recent_items(days=days)

        return jsonify([{
            'id': i.id,
            'feed_id': i.feed_id,
            'title': i.title,
            'link': i.link,
            'summary': i.summary[:200],
            'published': i.published.isoformat(),
            'relevance': i.relevance_score,
            'frameworks': i.frameworks_affected
        } for i in items[:50]])

    # -------------------------------------------------------------------------
    # ERROR HANDLERS
    # -------------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500

    return app


def main():
    """Run the development server"""
    if not FLASK_AVAILABLE:
        logger.error("Flask not installed. Run: pip install flask")
        return

    app_config = get_config()
    app = create_app()

    logger.info("PolicyUpdate Web Interface")
    logger.info("=" * 40)
    logger.info(f"Starting server at http://{app_config.web.host}:{app_config.web.port}")
    logger.info("Press Ctrl+C to stop")

    app.run(
        debug=app_config.web.debug,
        host=app_config.web.host,
        port=app_config.web.port
    )


if __name__ == '__main__':
    main()
