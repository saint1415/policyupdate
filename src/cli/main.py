#!/usr/bin/env python3
"""
PolicyUpdate CLI
Command-line interface for the GRC policy management platform

Usage:
    policy-grc policies list
    policy-grc policies search <query>
    policy-grc frameworks list
    policy-grc frameworks coverage <framework>
    policy-grc generate <client_name> --frameworks soc2,hipaa --output ./output
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add project root to path
CLI_DIR = Path(__file__).parent
PROJECT_ROOT = CLI_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False


def get_policies_dir():
    return PROJECT_ROOT / "policies"


def get_frameworks_dir():
    return PROJECT_ROOT / "config" / "frameworks"


def get_output_dir():
    return PROJECT_ROOT / "output"


# Initialize lazy-loaded modules
_compliance_mapper = None
_gap_analyzer = None
_package_builder = None


def get_compliance_mapper():
    global _compliance_mapper
    if _compliance_mapper is None:
        from core.compliance_mapper import ComplianceMapper
        _compliance_mapper = ComplianceMapper()
        _compliance_mapper.load_all_frameworks(str(get_frameworks_dir()))
    return _compliance_mapper


def get_gap_analyzer():
    global _gap_analyzer
    if _gap_analyzer is None:
        from core.gap_analyzer import GapAnalyzer
        _gap_analyzer = GapAnalyzer(compliance_mapper=get_compliance_mapper())
        _gap_analyzer.load_policy_library_from_dir(str(get_policies_dir()))
    return _gap_analyzer


def get_package_builder():
    global _package_builder
    if _package_builder is None:
        from generation.package_builder import PackageBuilder
        _package_builder = PackageBuilder(
            str(get_policies_dir()),
            str(get_frameworks_dir())
        )
    return _package_builder


if CLICK_AVAILABLE:
    @click.group()
    @click.version_option(version="1.0.0", prog_name="policy-grc")
    def cli():
        """PolicyUpdate - GRC Policy Management Platform

        Generate compliance-mapped policy packages for your organization.
        """
        pass

    # =========================================================================
    # POLICIES COMMANDS
    # =========================================================================
    @cli.group()
    def policies():
        """Manage policy library"""
        pass

    @policies.command("list")
    @click.option("--category", "-c", help="Filter by category")
    @click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
    def policies_list(category, format):
        """List all policies in the library"""
        builder = get_package_builder()
        all_policies = builder.get_all_policies()

        if category:
            all_policies = {
                k: v for k, v in all_policies.items()
                if v.get("category", "").lower() == category.lower()
            }

        if format == "json":
            output = [
                {"id": p["id"], "title": p["title"], "category": p["category"]}
                for p in all_policies.values()
            ]
            click.echo(json.dumps(output, indent=2))
        else:
            # Group by category
            categories = {}
            for policy in all_policies.values():
                cat = policy.get("category", "uncategorized")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(policy)

            click.echo(f"\nPolicy Library ({len(all_policies)} policies)")
            click.echo("=" * 60)

            for cat in sorted(categories.keys()):
                click.echo(f"\n{cat.replace('-', ' ').title()} ({len(categories[cat])})")
                click.echo("-" * 40)
                for p in sorted(categories[cat], key=lambda x: x["title"]):
                    click.echo(f"  {p['id']}")

    @policies.command("search")
    @click.argument("query")
    def policies_search(query):
        """Search policies by title or content"""
        builder = get_package_builder()
        all_policies = builder.get_all_policies()

        query_lower = query.lower()
        results = []

        for policy in all_policies.values():
            if (query_lower in policy["id"].lower() or
                query_lower in policy.get("title", "").lower() or
                query_lower in policy.get("body", "").lower()):
                results.append(policy)

        click.echo(f"\nSearch results for '{query}' ({len(results)} found)")
        click.echo("=" * 60)

        for p in sorted(results, key=lambda x: x["title"]):
            frameworks = list(p.get("frameworks", {}).keys())
            fw_str = f" [{', '.join(frameworks)}]" if frameworks else ""
            click.echo(f"  {p['id']}: {p['title']}{fw_str}")

    @policies.command("validate")
    def policies_validate():
        """Validate all policies"""
        builder = get_package_builder()
        all_policies = builder.get_all_policies()

        click.echo(f"\nValidating {len(all_policies)} policies...")
        click.echo("=" * 60)

        errors = []
        warnings = []

        for policy_id, policy in all_policies.items():
            # Check for required fields
            if not policy.get("title"):
                errors.append(f"{policy_id}: Missing title")
            if not policy.get("category"):
                warnings.append(f"{policy_id}: Missing category")

            # Check for unreplaced variables
            body = policy.get("body", "")
            import re
            unreplaced = re.findall(r'\{\{([A-Z_]+)\}\}', body)
            if unreplaced:
                click.echo(f"  {policy_id}: Variables to replace: {', '.join(set(unreplaced))}")

        if errors:
            click.echo(f"\nErrors ({len(errors)}):")
            for e in errors:
                click.echo(f"  [ERROR] {e}")

        if warnings:
            click.echo(f"\nWarnings ({len(warnings)}):")
            for w in warnings[:10]:
                click.echo(f"  [WARN]  {w}")

        click.echo(f"\n[OK] Validation complete: {len(all_policies)} policies checked")

    # =========================================================================
    # FRAMEWORKS COMMANDS
    # =========================================================================
    @cli.group()
    def frameworks():
        """Manage compliance frameworks"""
        pass

    @frameworks.command("list")
    def frameworks_list():
        """List all available frameworks"""
        mapper = get_compliance_mapper()

        click.echo("\nAvailable Compliance Frameworks")
        click.echo("=" * 60)

        for fw_id, framework in sorted(mapper.frameworks.items()):
            summary = mapper.get_framework_summary(fw_id)
            click.echo(f"\n{fw_id.upper()}: {framework.name}")
            click.echo(f"  Version: {framework.version}")
            click.echo(f"  Controls: {summary['total_controls']}")
            click.echo(f"  Required Policies: {summary['required_policies']}")

    @frameworks.command("coverage")
    @click.argument("framework_id")
    def frameworks_coverage(framework_id):
        """Show coverage analysis for a framework"""
        analyzer = get_gap_analyzer()

        try:
            report = analyzer.analyze_framework(framework_id)
        except ValueError as e:
            click.echo(f"Error: {e}")
            return

        click.echo(f"\n{report.framework_name} Coverage Analysis")
        click.echo("=" * 60)
        click.echo(f"Total Controls: {report.total_controls}")
        click.echo(f"Fully Covered: {report.fully_covered_controls} ({report.overall_coverage * 100:.1f}%)")
        click.echo(f"Partially Covered: {report.partially_covered_controls}")
        click.echo(f"Not Covered: {report.not_covered_controls}")
        click.echo(f"Required Policies: {report.total_required_policies}")
        click.echo(f"Missing Policies: {report.missing_policies}")

        if report.missing_policy_list:
            click.echo(f"\nMissing Policies:")
            for p in report.missing_policy_list[:10]:
                click.echo(f"  - {p}")

    @frameworks.command("gaps")
    @click.option("--frameworks", "-f", help="Comma-separated framework IDs")
    def frameworks_gaps(frameworks):
        """Show gaps across frameworks"""
        analyzer = get_gap_analyzer()
        mapper = get_compliance_mapper()

        if frameworks:
            fw_list = [f.strip() for f in frameworks.split(",")]
        else:
            fw_list = list(mapper.frameworks.keys())

        click.echo("\nCross-Framework Gap Analysis")
        click.echo("=" * 60)

        priorities = analyzer.generate_remediation_priorities(fw_list, limit=15)

        if not priorities:
            click.echo("\n[OK] No gaps found! All frameworks have 100% policy coverage.")
            return

        click.echo(f"\nTop {len(priorities)} policies to create:\n")
        for i, item in enumerate(priorities, 1):
            click.echo(f"{i}. [{item['priority'].upper()}] {item['policy_id']}")
            click.echo(f"   Impacts: {item['frameworks_impacted']} frameworks, {item['controls_impacted']} controls")

    # =========================================================================
    # GENERATE COMMAND
    # =========================================================================
    @cli.command()
    @click.argument("client_name")
    @click.option("--frameworks", "-f", help="Comma-separated framework IDs (e.g., soc2,hipaa)")
    @click.option("--output", "-o", type=click.Path(), help="Output directory")
    @click.option("--format", type=click.Choice(["docx", "md", "pdf", "html", "all"]), default="docx")
    @click.option("--org-name", help="Organization name (default: client_name)")
    @click.option("--cso-title", default="Chief Security Officer", help="CSO title")
    @click.option("--all-policies", is_flag=True, help="Include all policies regardless of framework")
    def generate(client_name, frameworks, output, format, org_name, cso_title, all_policies):
        """Generate a policy package for a client

        Example:
            policy-grc generate "Acme Corp" --frameworks soc2,hipaa --output ./output
        """
        from generation.package_builder import PackageBuilder, ClientConfig

        builder = get_package_builder()

        # Parse frameworks
        fw_list = []
        if frameworks:
            fw_list = [f.strip().lower() for f in frameworks.split(",")]

        # Build variables
        variables = {
            "ORGANIZATION_NAME": org_name or client_name,
            "CSO_TITLE": cso_title,
            "EXEC_MGMT": "Executive Management",
            "IT_STAFF": "IT Staff",
            "HR_DEPARTMENT": "Human Resources",
            "LEGAL_DEPARTMENT": "Legal Department",
            "RMO_TITLE": "Risk Management Officer"
        }

        config = ClientConfig(
            name=client_name,
            variables=variables,
            frameworks=fw_list
        )

        click.echo(f"\nGenerating policy package for: {client_name}")
        click.echo(f"Frameworks: {', '.join(fw_list) if fw_list else 'All'}")
        click.echo("-" * 50)

        result = builder.build_package(config, include_all=all_policies)

        click.echo(f"Total policies: {result.total_policies}")
        click.echo(f"Incomplete: {result.incomplete_count}")

        # Set output directory
        output_dir = Path(output) if output else get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = client_name.lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d")

        # Export DOCX
        if format in ["docx", "all"]:
            try:
                from generation.docx_exporter import DocxExporter
                exporter = DocxExporter()

                docx_path = output_dir / f"{safe_name}_policies_{timestamp}.docx"
                exporter.export_package(result, str(docx_path))
                click.echo(f"\n[OK] DOCX exported: {docx_path}")
            except ImportError:
                click.echo("\n[WARN] python-docx not installed. Run: pip install python-docx")

        # Export PDF
        if format in ["pdf", "all"]:
            try:
                from generation.pdf_exporter import PdfExporter
                pdf_exporter = PdfExporter()

                pdf_path = output_dir / f"{safe_name}_policies_{timestamp}.pdf"
                pdf_exporter.export_package(result, str(pdf_path))
                click.echo(f"[OK] PDF exported: {pdf_path}")
            except ImportError as e:
                click.echo(f"\n[WARN] PDF export unavailable: {e}")
                click.echo("       Install with: pip install weasyprint")

        # Export HTML
        if format in ["html", "all"]:
            from generation.html_exporter import HtmlExporter
            html_exporter = HtmlExporter()

            html_path = output_dir / f"{safe_name}_policies_{timestamp}.html"
            html_exporter.export_package(result, str(html_path))
            click.echo(f"[OK] HTML exported: {html_path}")

        # Export Markdown
        if format in ["md", "all"]:
            md_dir = output_dir / f"{safe_name}_policies_{timestamp}"
            md_dir.mkdir(exist_ok=True)

            # Write TOC
            toc = builder.generate_table_of_contents(result)
            (md_dir / "00_TABLE_OF_CONTENTS.md").write_text(toc, encoding="utf-8")

            # Write checklist
            checklist = builder.generate_customization_checklist(result)
            (md_dir / "00_CUSTOMIZATION_CHECKLIST.md").write_text(checklist, encoding="utf-8")

            # Write each policy
            for policy in result.policies:
                safe_id = policy.id.replace("/", "_")
                policy_file = md_dir / f"{policy.category}_{safe_id}.md"
                content = f"# {policy.title}\n\n{policy.content}"
                policy_file.write_text(content, encoding="utf-8")

            click.echo(f"[OK] Markdown exported: {md_dir}")

        if result.warnings:
            click.echo(f"\n[WARN]  {len(result.warnings)} warnings (missing cross-references)")

    # =========================================================================
    # REPORT COMMAND
    # =========================================================================
    @cli.group()
    def report():
        """Generate reports"""
        pass

    @report.command("compliance")
    @click.option("--frameworks", "-f", help="Comma-separated framework IDs")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    def report_compliance(frameworks, output):
        """Generate a compliance coverage report"""
        analyzer = get_gap_analyzer()
        mapper = get_compliance_mapper()

        if frameworks:
            fw_list = [f.strip() for f in frameworks.split(",")]
        else:
            fw_list = list(mapper.frameworks.keys())

        lines = [
            "# Compliance Coverage Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Summary",
            "",
            "| Framework | Controls | Coverage | Missing |",
            "|-----------|----------|----------|---------|"
        ]

        for fw_id in fw_list:
            try:
                report = analyzer.analyze_framework(fw_id)
                coverage_pct = f"{report.overall_coverage * 100:.0f}%"
                lines.append(
                    f"| {report.framework_name} | {report.total_controls} | "
                    f"{coverage_pct} | {report.missing_policies} |"
                )
            except ValueError:
                continue

        content = "\n".join(lines)

        if output:
            Path(output).write_text(content, encoding="utf-8")
            click.echo(f"Report saved to: {output}")
        else:
            click.echo(content)


    # =========================================================================
    # CLIENTS COMMANDS
    # =========================================================================
    @cli.group()
    def clients():
        """Manage client profiles"""
        pass

    def get_client_manager():
        from crm.client_manager import ClientManager
        db_path = PROJECT_ROOT / "data" / "clients.db"
        return ClientManager(str(db_path))

    @clients.command("list")
    def clients_list():
        """List all clients"""
        manager = get_client_manager()
        clients = manager.list_clients()

        if not clients:
            click.echo("\nNo clients found. Create one with: policy-grc clients add <name>")
            return

        click.echo(f"\nClients ({len(clients)})")
        click.echo("=" * 60)
        for client in clients:
            fw_str = ", ".join(client.target_frameworks) if client.target_frameworks else "none"
            click.echo(f"\n  {client.id}: {client.name}")
            click.echo(f"     Industry: {client.industry or 'N/A'}")
            click.echo(f"     Size: {client.size_tier}")
            click.echo(f"     Frameworks: {fw_str}")

    @clients.command("add")
    @click.argument("name")
    @click.option("--industry", "-i", help="Industry (technology, healthcare, finance, etc.)")
    @click.option("--size", "-s", type=click.Choice(["solopreneur", "small", "medium", "enterprise"]), default="medium")
    @click.option("--frameworks", "-f", help="Target frameworks (comma-separated)")
    @click.option("--contact", help="Primary contact name")
    @click.option("--email", help="Primary contact email")
    def clients_add(name, industry, size, frameworks, contact, email):
        """Add a new client"""
        manager = get_client_manager()

        fw_list = [f.strip() for f in frameworks.split(",")] if frameworks else []

        client = manager.create_client(
            name,
            industry=industry or "",
            size_tier=size,
            target_frameworks=fw_list,
            primary_contact_name=contact or "",
            primary_contact_email=email or ""
        )

        click.echo(f"\n[OK] Created client: {client.name} (ID: {client.id})")
        if fw_list:
            click.echo(f"     Target frameworks: {', '.join(fw_list)}")

    @clients.command("show")
    @click.argument("client_id")
    def clients_show(client_id):
        """Show client details"""
        manager = get_client_manager()
        summary = manager.get_client_summary(client_id)

        if "error" in summary:
            # Try by name
            client = manager.get_client_by_name(client_id)
            if client:
                summary = manager.get_client_summary(client.id)
            else:
                click.echo(f"Error: Client not found: {client_id}")
                return

        c = summary["client"]
        click.echo(f"\n{c['name']}")
        click.echo("=" * 50)
        click.echo(f"ID: {c['id']}")
        click.echo(f"Industry: {c['industry'] or 'N/A'}")
        click.echo(f"Size: {c['size_tier']} ({c['employee_count']} employees)")
        click.echo(f"Contact: {c['primary_contact_name']} <{c['primary_contact_email']}>")
        click.echo(f"Frameworks: {', '.join(c['target_frameworks']) or 'None'}")

        click.echo(f"\nVariables:")
        for k, v in c.get('variables', {}).items():
            click.echo(f"  {k}: {v}")

        g = summary["generations"]
        click.echo(f"\nGenerations: {g['total']} ({g['total_policies_generated']} total policies)")
        if g['latest']:
            click.echo(f"  Last generated: {g['latest'][:10]}")

        comp = summary["compliance"]
        click.echo(f"\nCompliance Status:")
        click.echo(f"  Tracked: {comp['frameworks_tracked']} frameworks")
        click.echo(f"  Compliant: {comp['compliant']}, Partial: {comp['partial']}, Non-compliant: {comp['non_compliant']}")

    @clients.command("set-var")
    @click.argument("client_id")
    @click.argument("variable")
    @click.argument("value")
    def clients_set_var(client_id, variable, value):
        """Set a variable for a client"""
        manager = get_client_manager()
        client = manager.get_client(client_id) or manager.get_client_by_name(client_id)

        if not client:
            click.echo(f"Error: Client not found: {client_id}")
            return

        variables = client.variables.copy()
        variables[variable] = value
        manager.update_client(client.id, variables=variables)

        click.echo(f"[OK] Set {variable}={value} for {client.name}")

    @clients.command("delete")
    @click.argument("client_id")
    @click.confirmation_option(prompt="Are you sure you want to delete this client?")
    def clients_delete(client_id):
        """Delete a client"""
        manager = get_client_manager()
        client = manager.get_client(client_id) or manager.get_client_by_name(client_id)

        if not client:
            click.echo(f"Error: Client not found: {client_id}")
            return

        manager.delete_client(client.id)
        click.echo(f"[OK] Deleted client: {client.name}")


    # =========================================================================
    # MONITOR COMMANDS
    # =========================================================================
    @cli.group()
    def monitor():
        """Monitor compliance framework updates"""
        pass

    def get_feed_monitor():
        from automation.feed_monitor import FeedMonitor
        db_path = PROJECT_ROOT / "data" / "feeds.db"
        return FeedMonitor(str(db_path))

    def get_change_detector():
        from automation.change_detector import ChangeDetector
        db_path = PROJECT_ROOT / "data" / "changes.db"
        policies_dir = PROJECT_ROOT / "policies"
        return ChangeDetector(str(db_path), str(policies_dir))

    @monitor.command("setup")
    def monitor_setup():
        """Set up default compliance feeds"""
        fm = get_feed_monitor()
        count = fm.load_default_feeds()
        click.echo(f"\n[OK] Loaded {count} default compliance feeds")

        feeds = fm.get_feeds()
        click.echo(f"\nConfigured Feeds:")
        for feed in feeds:
            click.echo(f"  - {feed.id}: {feed.name}")
            click.echo(f"    Frameworks: {', '.join(feed.frameworks)}")

    @monitor.command("feeds")
    def monitor_feeds():
        """List configured feeds"""
        fm = get_feed_monitor()
        feeds = fm.get_feeds(enabled_only=False)

        if not feeds:
            click.echo("\nNo feeds configured. Run: policy-grc monitor setup")
            return

        click.echo(f"\nConfigured Feeds ({len(feeds)})")
        click.echo("=" * 60)

        for feed in feeds:
            status = "[ON]" if feed.enabled else "[OFF]"
            click.echo(f"\n  {status} {feed.id}: {feed.name}")
            click.echo(f"      URL: {feed.url[:50]}...")
            click.echo(f"      Interval: {feed.check_interval}")
            click.echo(f"      Keywords: {', '.join(feed.keywords[:3])}{'...' if len(feed.keywords) > 3 else ''}")
            click.echo(f"      Frameworks: {', '.join(feed.frameworks)}")

    @monitor.command("check")
    @click.option("--feed", "-f", help="Check specific feed ID")
    def monitor_check(feed):
        """Check feeds for updates"""
        fm = get_feed_monitor()

        try:
            import feedparser
        except ImportError:
            click.echo("[ERROR] feedparser not installed. Run: pip install feedparser")
            return

        click.echo("\nChecking feeds for updates...")

        if feed:
            items = fm.check_feed(feed)
            click.echo(f"\nFound {len(items)} new items from {feed}")
        else:
            items = fm.check_all_feeds()
            click.echo(f"\nFound {len(items)} new items across all feeds")

        if items:
            click.echo("\nNew Items:")
            for item in items[:10]:
                score_str = f"[{item.relevance_score:.1f}]"
                click.echo(f"\n  {score_str} {item.title[:60]}...")
                if item.frameworks_affected:
                    click.echo(f"        Frameworks: {', '.join(item.frameworks_affected)}")
                click.echo(f"        Source: {item.feed_id}")

            if len(items) > 10:
                click.echo(f"\n  ... and {len(items) - 10} more items")

    @monitor.command("analyze")
    @click.option("--days", "-d", default=7, help="Days to analyze")
    def monitor_analyze(days):
        """Analyze updates for policy impacts"""
        detector = get_change_detector()

        click.echo(f"\nAnalyzing updates from last {days} days...")
        alerts = detector.analyze_recent_updates(days=days)

        click.echo(f"\nGenerated {len(alerts)} alerts")

        if alerts:
            # Group by severity
            by_severity = {}
            for alert in alerts:
                if alert.severity not in by_severity:
                    by_severity[alert.severity] = []
                by_severity[alert.severity].append(alert)

            click.echo("\nBy Severity:")
            for severity in ["critical", "high", "medium", "low"]:
                if severity in by_severity:
                    click.echo(f"  {severity.upper()}: {len(by_severity[severity])}")

    @monitor.command("alerts")
    @click.option("--severity", "-s", type=click.Choice(["critical", "high", "medium", "low"]))
    def monitor_alerts(severity):
        """Show pending change alerts"""
        detector = get_change_detector()
        alerts = detector.get_pending_alerts()

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if not alerts:
            click.echo("\n[OK] No pending alerts")
            return

        click.echo(f"\nPending Alerts ({len(alerts)})")
        click.echo("=" * 60)

        for alert in alerts[:15]:
            click.echo(f"\n  [{alert.severity.upper()}] {alert.title[:55]}...")
            click.echo(f"  ID: {alert.id}")
            click.echo(f"  Type: {alert.change_type}")
            click.echo(f"  Frameworks: {', '.join(alert.frameworks_affected)}")
            click.echo(f"  Policies Affected: {len(alert.policy_impacts)}")

        if len(alerts) > 15:
            click.echo(f"\n  ... and {len(alerts) - 15} more alerts")

    @monitor.command("report")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    def monitor_report(output):
        """Generate change alert report"""
        detector = get_change_detector()
        report = detector.generate_alert_report()

        if output:
            Path(output).write_text(report, encoding="utf-8")
            click.echo(f"[OK] Report saved to: {output}")
        else:
            click.echo(report)

    @monitor.command("acknowledge")
    @click.argument("alert_id")
    @click.option("--notes", "-n", help="Notes about acknowledgment")
    def monitor_acknowledge(alert_id, notes):
        """Acknowledge a change alert"""
        detector = get_change_detector()
        detector.acknowledge_alert(alert_id, notes or "")
        click.echo(f"[OK] Alert {alert_id} acknowledged")

    @monitor.command("resolve")
    @click.argument("alert_id")
    @click.option("--notes", "-n", help="Resolution notes")
    def monitor_resolve(alert_id, notes):
        """Mark a change alert as resolved"""
        detector = get_change_detector()
        detector.resolve_alert(alert_id, notes or "")
        click.echo(f"[OK] Alert {alert_id} resolved")


def main():
    if not CLICK_AVAILABLE:
        print("Error: click library required. Install with: pip install click")
        print("\nBasic usage without click:")
        print("  python -m src.cli.main --help")
        sys.exit(1)

    cli()


if __name__ == "__main__":
    main()
