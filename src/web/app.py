"""
Flask Web Application
Web interface for the GRC Policy Management Platform
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
WEB_DIR = Path(__file__).parent
PROJECT_ROOT = WEB_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from core.config import get_config, setup_logging, get_logger
from core.validation import sanitize_filename, validate_path

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

    # Initialize Flask-Login
    try:
        from flask_login import LoginManager, current_user
        from web.auth import AuthManager, User

        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'

        auth_manager = AuthManager(str(PROJECT_ROOT / "data" / "users.db"))

        @login_manager.user_loader
        def load_user(user_id):
            return auth_manager.get_user(user_id)

        # Register auth blueprint
        from web.auth_routes import create_auth_blueprint
        auth_bp = create_auth_blueprint(auth_manager)
        app.register_blueprint(auth_bp, url_prefix='/auth')

        HAS_AUTH = True
    except ImportError:
        HAS_AUTH = False
        current_user = None
        logger.warning("Flask-Login not available, running without authentication")

    # Initialize rate limiting
    try:
        from web.rate_limiter import init_rate_limiter, RateLimitConfig
        rate_config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            auth_multiplier=2.0,
            exempt_paths=['/auth/login', '/api/health', '/static', '/']
        )
        init_rate_limiter(app, rate_config)
        logger.info("Rate limiting initialized")
    except ImportError:
        logger.warning("Rate limiter not available")

    # Initialize audit logging
    try:
        from core.audit import AuditLogger, AuditAction
        audit_logger = AuditLogger(str(PROJECT_ROOT / "data" / "audit.db"))
        HAS_AUDIT = True
    except ImportError:
        HAS_AUDIT = False
        audit_logger = None

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

    def get_version_manager():
        if 'versions' not in _cache:
            from core.versioning import PolicyVersionManager
            _cache['versions'] = PolicyVersionManager(str(PROJECT_ROOT / "data" / "versions.db"))
        return _cache['versions']

    # Context processor for templates
    @app.context_processor
    def inject_globals():
        return {
            'current_user': current_user if HAS_AUTH else None,
            'has_auth': HAS_AUTH
        }

    # =========================================================================
    # PAGE ROUTES
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

    @app.route('/policies')
    def policies_page():
        """Policies browser page"""
        builder = get_package_builder()
        mapper = get_compliance_mapper()

        policies = builder.get_all_policies()

        # Get unique categories
        categories = sorted(set(p.get('category', '') for p in policies.values() if p.get('category')))

        # Get frameworks for filter
        frameworks = [
            {'id': fw_id, 'name': fw.name}
            for fw_id, fw in mapper.frameworks.items()
        ]

        # Transform policies for template
        policy_list = []
        for pid, policy in policies.items():
            policy_list.append({
                'id': policy.get('id', pid),
                'title': policy.get('title', ''),
                'category': policy.get('category', ''),
                'frameworks': list(policy.get('frameworks', {}).keys())
            })

        policy_list.sort(key=lambda x: (x['category'], x['title']))

        return render_template('policies.html',
            policies=policy_list,
            categories=categories,
            frameworks=frameworks,
            total_policies=len(policies)
        )

    @app.route('/frameworks')
    def frameworks_page():
        """Frameworks viewer page"""
        mapper = get_compliance_mapper()
        analyzer = get_gap_analyzer()

        frameworks = []
        total_controls = 0

        for fw_id, framework in mapper.frameworks.items():
            summary = mapper.get_framework_summary(fw_id)

            # Get coverage
            try:
                report = analyzer.analyze_framework(fw_id)
                coverage = round(report.overall_coverage * 100, 1)
            except:
                coverage = 0

            total_controls += summary['total_controls']

            frameworks.append({
                'id': fw_id,
                'name': framework.name,
                'version': framework.version,
                'organization': getattr(framework, 'organization', None),
                'controls': summary['total_controls'],
                'required_policies': summary['required_policies'],
                'coverage': coverage
            })

        frameworks.sort(key=lambda x: x['name'])

        return render_template('frameworks.html',
            frameworks=frameworks,
            total_controls=total_controls,
            total_policies=len(get_package_builder().get_all_policies())
        )

    @app.route('/clients')
    def clients_page():
        """Client management page"""
        manager = get_client_manager()
        mapper = get_compliance_mapper()

        clients = manager.list_clients()

        # Get frameworks for form
        frameworks = [
            {'id': fw_id, 'name': fw.name}
            for fw_id, fw in mapper.frameworks.items()
        ]

        return render_template('clients.html',
            clients=clients,
            frameworks=sorted(frameworks, key=lambda x: x['name'])
        )

    @app.route('/generate')
    def generate_page():
        """Package generation page"""
        manager = get_client_manager()
        mapper = get_compliance_mapper()

        clients = manager.list_clients()

        # Get frameworks
        frameworks = []
        for fw_id, framework in mapper.frameworks.items():
            summary = mapper.get_framework_summary(fw_id)
            frameworks.append({
                'id': fw_id,
                'name': framework.name,
                'controls': summary['total_controls']
            })

        frameworks.sort(key=lambda x: x['name'])

        # Check for preselected client
        selected_client = request.args.get('client', '')

        return render_template('generate.html',
            clients=clients,
            frameworks=frameworks,
            selected_client=selected_client
        )

    @app.route('/monitor')
    def monitor_page():
        """Monitoring dashboard page"""
        monitor = get_feed_monitor()

        feeds = monitor.get_feeds(enabled_only=False)
        recent_items = monitor.get_recent_items(days=7)

        # Transform items for template
        items = []
        for item in recent_items[:20]:
            items.append({
                'id': item.id,
                'title': item.title,
                'link': item.link,
                'summary': item.summary,
                'published': item.published.strftime('%Y-%m-%d %H:%M') if item.published else 'Unknown',
                'relevance': item.relevance_score,
                'frameworks': item.frameworks_affected,
                'feed_name': item.feed_id
            })

        # Get feed list for config
        feed_list = []
        for feed in feeds:
            feed_list.append({
                'id': feed.id,
                'name': feed.name,
                'type': feed.feed_type,
                'enabled': feed.enabled,
                'frameworks': feed.frameworks
            })

        return render_template('monitor.html',
            feeds=feed_list,
            recent_items=items,
            alerts=[],  # TODO: Implement alerts
            last_check=datetime.now().strftime('%Y-%m-%d %H:%M'),
            pending_alerts=0,
            updates_available=len(items),
            active_feeds=sum(1 for f in feeds if f.enabled),
            frameworks_monitored=len(set(fw for f in feeds for fw in f.frameworks))
        )

    @app.route('/audit')
    def audit_page():
        """Audit log viewer page"""
        if not HAS_AUDIT:
            return render_template('audit.html',
                logs=[],
                stats={'critical': 0, 'warnings': 0, 'total_today': 0, 'unique_users': 0},
                page=1,
                total_pages=1
            )

        # Get filter parameters
        page = request.args.get('page', 1, type=int)
        severity = request.args.get('severity', '')
        action = request.args.get('action', '')
        search = request.args.get('q', '')

        per_page = 50
        offset = (page - 1) * per_page

        # Get logs
        logs = audit_logger.get_logs(
            limit=per_page,
            offset=offset,
            severity=severity if severity else None,
            action_filter=action if action else None
        )

        # Get stats
        stats = audit_logger.get_statistics(days=1)

        # Calculate total pages (approximate)
        total_logs = stats.get('total_events', 0)
        total_pages = max(1, (total_logs + per_page - 1) // per_page)

        # Transform logs for template
        log_list = []
        for log in logs:
            # Determine action category for styling
            action_str = log.get('action', '')
            if 'LOGIN' in action_str or 'LOGOUT' in action_str:
                action_cat = 'auth'
            elif 'GENERATE' in action_str or 'EXPORT' in action_str:
                action_cat = 'generate'
            elif 'CLIENT' in action_str:
                action_cat = 'data'
            else:
                action_cat = 'system'

            log_list.append({
                'id': log.get('id', ''),
                'timestamp': log.get('timestamp', ''),
                'severity': log.get('severity', 'info').lower(),
                'action': action_str,
                'action_category': action_cat,
                'username': log.get('username', ''),
                'details': log.get('details', ''),
                'ip_address': log.get('ip_address', '')
            })

        return render_template('audit.html',
            logs=log_list,
            stats={
                'critical': stats.get('by_severity', {}).get('CRITICAL', 0),
                'warnings': stats.get('by_severity', {}).get('WARNING', 0),
                'total_today': sum(stats.get('by_severity', {}).values()),
                'unique_users': stats.get('unique_users', 0)
            },
            page=page,
            total_pages=total_pages
        )

    # =========================================================================
    # POLICIES API
    # =========================================================================

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

    # =========================================================================
    # FRAMEWORKS API
    # =========================================================================

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

    # =========================================================================
    # CLIENTS API
    # =========================================================================

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

        # Audit log
        if HAS_AUDIT and audit_logger:
            audit_logger.log(
                action=AuditAction.CLIENT_CREATE,
                resource_type='client',
                resource_id=client.id,
                details=f"Created client: {client.name}",
                username=current_user.username if HAS_AUTH and current_user else None,
                ip_address=request.remote_addr
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

    @app.route('/api/clients/<client_id>', methods=['PUT'])
    def api_update_client(client_id):
        """Update a client"""
        data = request.get_json()
        manager = get_client_manager()

        client = manager.get_client(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        # Update fields
        if 'name' in data:
            client.name = data['name']
        if 'industry' in data:
            client.industry = data['industry']
        if 'size_tier' in data:
            client.size_tier = data['size_tier']
        if 'frameworks' in data:
            client.target_frameworks = data['frameworks']

        manager.update_client(client)

        return jsonify({'message': 'Client updated'})

    @app.route('/api/clients/<client_id>', methods=['DELETE'])
    def api_delete_client(client_id):
        """Delete a client"""
        manager = get_client_manager()
        manager.delete_client(client_id)

        # Audit log
        if HAS_AUDIT and audit_logger:
            audit_logger.log(
                action=AuditAction.CLIENT_DELETE,
                resource_type='client',
                resource_id=client_id,
                details=f"Deleted client",
                username=current_user.username if HAS_AUTH and current_user else None,
                ip_address=request.remote_addr
            )

        return jsonify({'message': 'Client deleted'})

    @app.route('/api/clients/<client_id>/variables', methods=['POST'])
    def api_set_client_variable(client_id):
        """Set a client variable"""
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Variable name required'}), 400

        manager = get_client_manager()
        manager.set_variable(client_id, data['name'], data.get('value', ''))

        return jsonify({'message': 'Variable set'})

    # =========================================================================
    # GENERATION API
    # =========================================================================

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

        safe_name = sanitize_filename(data['client_name'].lower().replace(' ', '_'))
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

        if output_format in ['html', 'all']:
            try:
                from generation.html_exporter import HtmlExporter
                exporter = HtmlExporter()
                html_path = output_dir / f"{safe_name}_{timestamp}.html"
                exporter.export_package(result, str(html_path))
                response_data['files'].append({
                    'format': 'html',
                    'filename': html_path.name,
                    'path': str(html_path)
                })
            except ImportError:
                response_data['html_error'] = 'HTML exporter not available'

        # Audit log
        if HAS_AUDIT and audit_logger:
            audit_logger.log(
                action=AuditAction.PACKAGE_GENERATE,
                resource_type='package',
                resource_id=safe_name,
                details=f"Generated {result.total_policies} policies for {data['client_name']}",
                username=current_user.username if HAS_AUTH and current_user else None,
                ip_address=request.remote_addr
            )

        return jsonify(response_data)

    @app.route('/api/download/<filename>')
    def api_download(filename):
        """Download a generated file"""
        # Validate filename to prevent path traversal
        try:
            safe_filename = sanitize_filename(filename)
        except:
            return jsonify({'error': 'Invalid filename'}), 400

        output_dir = PROJECT_ROOT / "output"
        file_path = output_dir / safe_filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        # Audit log
        if HAS_AUDIT and audit_logger:
            audit_logger.log(
                action=AuditAction.FILE_DOWNLOAD,
                resource_type='file',
                resource_id=safe_filename,
                details=f"Downloaded file: {safe_filename}",
                username=current_user.username if HAS_AUTH and current_user else None,
                ip_address=request.remote_addr
            )

        return send_file(str(file_path), as_attachment=True)

    # =========================================================================
    # MONITORING API
    # =========================================================================

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
            'summary': i.summary[:200] if i.summary else '',
            'published': i.published.isoformat() if i.published else None,
            'relevance': i.relevance_score,
            'frameworks': i.frameworks_affected
        } for i in items[:50]])

    @app.route('/api/monitor/check', methods=['POST'])
    def api_monitor_check():
        """Trigger a feed check"""
        monitor = get_feed_monitor()

        try:
            results = monitor.check_all_feeds()
            return jsonify({
                'message': f'Checked {len(results)} feeds',
                'new_items': sum(r.get('new_items', 0) for r in results)
            })
        except Exception as e:
            logger.error(f"Feed check failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/monitor/setup', methods=['POST'])
    def api_monitor_setup():
        """Setup default feeds"""
        monitor = get_feed_monitor()

        try:
            monitor.setup_default_feeds()
            return jsonify({'message': 'Default feeds configured'})
        except Exception as e:
            logger.error(f"Feed setup failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/monitor/feeds/<feed_id>/toggle', methods=['POST'])
    def api_toggle_feed(feed_id):
        """Toggle a feed's enabled status"""
        data = request.get_json()
        enabled = data.get('enabled', True)

        monitor = get_feed_monitor()

        try:
            monitor.set_feed_enabled(feed_id, enabled)
            return jsonify({'message': f'Feed {"enabled" if enabled else "disabled"}'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # AUDIT API
    # =========================================================================

    @app.route('/api/audit/<log_id>')
    def api_audit_detail(log_id):
        """Get audit log details"""
        if not HAS_AUDIT:
            return jsonify({'error': 'Audit logging not available'}), 404

        logs = audit_logger.get_logs(limit=1000)
        log = next((l for l in logs if l.get('id') == log_id), None)

        if not log:
            return jsonify({'error': 'Log not found'}), 404

        return jsonify(log)

    @app.route('/api/audit/export')
    def api_audit_export():
        """Export audit logs"""
        if not HAS_AUDIT:
            return jsonify({'error': 'Audit logging not available'}), 404

        format_type = request.args.get('format', 'json')
        days = request.args.get('days', 30, type=int)

        logs = audit_logger.get_logs(limit=10000)

        if format_type == 'json':
            return jsonify(logs)
        elif format_type == 'csv':
            import csv
            import io

            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)

            response = app.make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=audit_logs.csv'
            return response

        return jsonify({'error': 'Invalid format'}), 400

    # =========================================================================
    # HEALTH & UTILITY
    # =========================================================================

    @app.route('/api/health')
    def api_health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500

    @app.errorhandler(429)
    def rate_limit_error(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

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
