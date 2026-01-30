"""
PDF Exporter Module
Exports policy packages to PDF format using WeasyPrint or ReportLab
"""

import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Try WeasyPrint first, fall back to basic HTML
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .package_builder import PackageResult, PolicyDocument


class PdfExporter:
    """
    Exports policy packages to PDF format.

    Usage:
        exporter = PdfExporter()
        exporter.export_package(result, "output/policies.pdf")
    """

    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "WeasyPrint is required for PDF export. "
                "Install it with: pip install weasyprint"
            )

    def _markdown_to_html(self, content: str) -> str:
        """Convert markdown content to HTML"""
        html = content

        # Headers
        html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
        html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Code
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        # Lists
        lines = html.split('\n')
        in_list = False
        result = []
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = re.sub(r'^[\s]*[-*]\s+', '', line)
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                if line.strip():
                    if not line.startswith('<h') and not line.startswith('<'):
                        result.append(f'<p>{line}</p>')
                    else:
                        result.append(line)
        if in_list:
            result.append('</ul>')

        return '\n'.join(result)

    def _get_css(self) -> str:
        """Get CSS styles for PDF"""
        return """
        @page {
            size: letter;
            margin: 1in;
            @top-center {
                content: string(title);
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
        }
        h1 {
            string-set: title content();
            color: #003366;
            font-size: 18pt;
            border-bottom: 2px solid #003366;
            padding-bottom: 10px;
            page-break-after: avoid;
        }
        h2 {
            color: #003366;
            font-size: 14pt;
            margin-top: 20px;
            page-break-after: avoid;
        }
        h3 {
            color: #444;
            font-size: 12pt;
            margin-top: 15px;
            page-break-after: avoid;
        }
        h4, h5, h6 {
            color: #555;
            margin-top: 10px;
            page-break-after: avoid;
        }
        p {
            margin: 10px 0;
            text-align: justify;
        }
        ul, ol {
            margin: 10px 0 10px 20px;
        }
        li {
            margin: 5px 0;
        }
        code {
            background: #f4f4f4;
            padding: 2px 5px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }
        .cover-page {
            text-align: center;
            padding-top: 200px;
            page-break-after: always;
        }
        .cover-title {
            font-size: 28pt;
            color: #003366;
            margin-bottom: 20px;
        }
        .cover-subtitle {
            font-size: 18pt;
            color: #666;
            margin-bottom: 50px;
        }
        .cover-info {
            font-size: 12pt;
            color: #666;
        }
        .toc {
            page-break-after: always;
        }
        .toc h1 {
            border-bottom: none;
        }
        .toc ul {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        .toc li {
            margin: 8px 0;
            padding-left: 20px;
        }
        .toc .category {
            font-weight: bold;
            color: #003366;
            margin-top: 15px;
            padding-left: 0;
        }
        .policy {
            page-break-before: always;
        }
        .policy-meta {
            background: #f9f9f9;
            padding: 10px;
            margin-bottom: 20px;
            border-left: 3px solid #003366;
            font-size: 10pt;
            color: #666;
        }
        .warning {
            color: #c00;
            font-weight: bold;
        }
        """

    def _generate_cover_html(self, result: PackageResult) -> str:
        """Generate cover page HTML"""
        frameworks = ', '.join(fw.upper() for fw in result.frameworks_covered) if result.frameworks_covered else 'All Frameworks'
        incomplete_note = f'<p class="warning">{result.incomplete_count} policies require customization</p>' if result.incomplete_count > 0 else ''

        return f'''
        <div class="cover-page">
            <div class="cover-title">{result.client_name}</div>
            <div class="cover-subtitle">Information Security Policy Package</div>
            <div class="cover-info">
                <p>Generated: {result.generated_at.strftime('%B %d, %Y')}</p>
                <p>Total Policies: {result.total_policies}</p>
                <p>Frameworks: {frameworks}</p>
                {incomplete_note}
            </div>
        </div>
        '''

    def _generate_toc_html(self, result: PackageResult) -> str:
        """Generate table of contents HTML"""
        # Group by category
        categories = {}
        for policy in result.policies:
            cat = policy.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(policy)

        toc_items = []
        for category in sorted(categories.keys()):
            toc_items.append(f'<li class="category">{category.replace("-", " ").title()}</li>')
            for policy in sorted(categories[category], key=lambda p: p.title):
                status = '<span class="warning">[!]</span> ' if policy.incomplete_sections else ''
                toc_items.append(f'<li>{status}{policy.title}</li>')

        return f'''
        <div class="toc">
            <h1>Table of Contents</h1>
            <ul>
                {''.join(toc_items)}
            </ul>
        </div>
        '''

    def _generate_policy_html(self, policy: PolicyDocument) -> str:
        """Generate HTML for a single policy"""
        content_html = self._markdown_to_html(policy.content)

        frameworks = ', '.join(policy.frameworks.keys()).upper() if policy.frameworks else 'N/A'
        meta = f'''
        <div class="policy-meta">
            <strong>Policy ID:</strong> {policy.id} |
            <strong>Category:</strong> {policy.category.replace("-", " ").title()} |
            <strong>Frameworks:</strong> {frameworks}
        </div>
        '''

        return f'''
        <div class="policy">
            <h1>{policy.title}</h1>
            {meta}
            {content_html}
        </div>
        '''

    def export_package(self, result: PackageResult, output_path: str):
        """
        Export a complete policy package to PDF.

        Args:
            result: PackageResult from PackageBuilder
            output_path: Path for the output PDF file
        """
        # Build HTML document
        html_parts = [
            '<!DOCTYPE html>',
            '<html><head><meta charset="utf-8"></head><body>',
            self._generate_cover_html(result),
            self._generate_toc_html(result),
        ]

        # Add each policy
        for policy in sorted(result.policies, key=lambda p: (p.category, p.title)):
            html_parts.append(self._generate_policy_html(policy))

        html_parts.append('</body></html>')
        html_content = '\n'.join(html_parts)

        # Generate PDF
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        html = HTML(string=html_content)
        css = CSS(string=self._get_css())
        html.write_pdf(str(output), stylesheets=[css])

        return output

    def export_single_policy(self, policy: PolicyDocument, output_path: str, client_name: str = ""):
        """Export a single policy to PDF"""
        html_content = f'''
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"></head><body>
        {self._generate_policy_html(policy)}
        </body></html>
        '''

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        html = HTML(string=html_content)
        css = CSS(string=self._get_css())
        html.write_pdf(str(output), stylesheets=[css])

        return output


def main():
    """Test the PDF exporter"""
    import sys
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    sys.path.insert(0, str(project_root / "src"))

    from generation.package_builder import PackageBuilder, ClientConfig

    policies_dir = project_root / "policies"
    frameworks_dir = project_root / "config" / "frameworks"
    output_dir = project_root / "output"

    print("=" * 60)
    print("PDF EXPORTER TEST")
    print("=" * 60)

    builder = PackageBuilder(str(policies_dir), str(frameworks_dir))

    config = ClientConfig(
        name="Acme Corporation",
        variables={
            "ORGANIZATION_NAME": "Acme Corporation",
            "CSO_TITLE": "Chief Information Security Officer",
        },
        frameworks=["soc2"]
    )

    print(f"\nBuilding package for: {config.name}")
    result = builder.build_package(config)
    print(f"Total policies: {result.total_policies}")

    try:
        exporter = PdfExporter()
        output_file = output_dir / f"{config.name.lower().replace(' ', '_')}_policies.pdf"

        print(f"\nExporting to: {output_file}")
        exporter.export_package(result, str(output_file))
        print(f"[OK] PDF export complete: {output_file}")

    except ImportError as e:
        print(f"\n[WARN] {e}")
        print("PDF export requires weasyprint. Install with: pip install weasyprint")


if __name__ == "__main__":
    main()
