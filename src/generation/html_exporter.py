"""
HTML Exporter Module
Exports policy packages to standalone HTML format
"""

import re
from pathlib import Path
from typing import Optional

from .package_builder import PackageResult, PolicyDocument


class HtmlExporter:
    """
    Exports policy packages to HTML format.

    Usage:
        exporter = HtmlExporter()
        exporter.export_package(result, "output/policies.html")
    """

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
        """Get CSS styles for HTML"""
        return """
        :root {
            --primary: #003366;
            --secondary: #0066cc;
            --light: #f8f9fa;
            --dark: #343a40;
            --border: #dee2e6;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 10px; margin: 30px 0 20px; }
        h2 { color: var(--primary); margin: 25px 0 15px; }
        h3 { color: #444; margin: 20px 0 10px; }
        h4, h5, h6 { color: #555; margin: 15px 0 10px; }
        p { margin: 10px 0; }
        ul, ol { margin: 10px 0 10px 30px; }
        li { margin: 5px 0; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .cover { text-align: center; padding: 60px 20px; margin-bottom: 40px; border-bottom: 3px solid var(--primary); }
        .cover-title { font-size: 2.5rem; color: var(--primary); margin-bottom: 10px; }
        .cover-subtitle { font-size: 1.5rem; color: #666; margin-bottom: 30px; }
        .cover-info { color: #666; }
        .toc { background: var(--light); padding: 20px; margin-bottom: 40px; border-radius: 8px; }
        .toc h2 { border: none; margin-top: 0; }
        .toc ul { list-style: none; margin: 0; padding: 0; }
        .toc li { margin: 8px 0; }
        .toc a { color: var(--secondary); text-decoration: none; }
        .toc a:hover { text-decoration: underline; }
        .toc .category { font-weight: bold; color: var(--primary); margin-top: 15px; }
        .policy { border-top: 1px solid var(--border); padding-top: 30px; margin-top: 30px; page-break-before: always; }
        .policy-meta { background: var(--light); padding: 15px; margin: 15px 0; border-left: 4px solid var(--primary); }
        .policy-meta strong { color: var(--primary); }
        .warning { color: #c00; font-weight: bold; }
        @media print {
            body { max-width: 100%; }
            .policy { page-break-before: always; }
            .toc { page-break-after: always; }
        }
        """

    def _generate_cover_html(self, result: PackageResult) -> str:
        """Generate cover page HTML"""
        frameworks = ', '.join(fw.upper() for fw in result.frameworks_covered) if result.frameworks_covered else 'All Frameworks'
        incomplete_note = f'<p class="warning">{result.incomplete_count} policies require customization</p>' if result.incomplete_count > 0 else ''

        return f'''
        <div class="cover">
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
                anchor = policy.id.replace('/', '-').replace(' ', '-')
                status = '<span class="warning">[!]</span> ' if policy.incomplete_sections else ''
                toc_items.append(f'<li>{status}<a href="#{anchor}">{policy.title}</a></li>')

        return f'''
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {''.join(toc_items)}
            </ul>
        </div>
        '''

    def _generate_policy_html(self, policy: PolicyDocument) -> str:
        """Generate HTML for a single policy"""
        content_html = self._markdown_to_html(policy.content)
        anchor = policy.id.replace('/', '-').replace(' ', '-')
        frameworks = ', '.join(policy.frameworks.keys()).upper() if policy.frameworks else 'N/A'

        meta = f'''
        <div class="policy-meta">
            <strong>Policy ID:</strong> {policy.id} |
            <strong>Category:</strong> {policy.category.replace("-", " ").title()} |
            <strong>Frameworks:</strong> {frameworks}
        </div>
        '''

        return f'''
        <div class="policy" id="{anchor}">
            <h1>{policy.title}</h1>
            {meta}
            {content_html}
        </div>
        '''

    def export_package(self, result: PackageResult, output_path: str):
        """
        Export a complete policy package to HTML.

        Args:
            result: PackageResult from PackageBuilder
            output_path: Path for the output HTML file
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<title>{result.client_name} - Policy Package</title>',
            '<style>',
            self._get_css(),
            '</style>',
            '</head>',
            '<body>',
            self._generate_cover_html(result),
            self._generate_toc_html(result),
        ]

        for policy in sorted(result.policies, key=lambda p: (p.category, p.title)):
            html_parts.append(self._generate_policy_html(policy))

        html_parts.extend([
            '</body>',
            '</html>'
        ])

        html_content = '\n'.join(html_parts)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html_content, encoding='utf-8')

        return output

    def export_single_policy(self, policy: PolicyDocument, output_path: str, client_name: str = ""):
        """Export a single policy to HTML"""
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="utf-8">
        <title>{policy.title}</title>
        <style>
        {self._get_css()}
        </style>
        </head>
        <body>
        {self._generate_policy_html(policy)}
        </body>
        </html>
        '''

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html_content, encoding='utf-8')

        return output


def main():
    """Test the HTML exporter"""
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
    print("HTML EXPORTER TEST")
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

    exporter = HtmlExporter()
    output_file = output_dir / f"{config.name.lower().replace(' ', '_')}_policies.html"

    print(f"\nExporting to: {output_file}")
    exporter.export_package(result, str(output_file))
    print(f"[OK] HTML export complete: {output_file}")


if __name__ == "__main__":
    main()
