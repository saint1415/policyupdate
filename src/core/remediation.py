"""
Remediation Reporter Module
Generates comprehensive remediation reports for clients
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class RemediationItem:
    """A single remediation action item"""
    id: str
    category: str  # policy_gap, incomplete_section, broken_reference, missing_evidence
    priority: str  # critical, high, medium, low
    policy_id: Optional[str]
    framework: Optional[str]
    description: str
    remediation: str
    estimated_effort: str = "Unknown"
    status: str = "open"  # open, in_progress, complete, waived


@dataclass
class RemediationReport:
    """Complete remediation report for a client"""
    client_id: str
    client_name: str
    generated_at: str
    target_frameworks: List[str]

    # Statistics
    policies_generated: int = 0
    policies_requiring_customization: int = 0
    critical_items: int = 0
    high_items: int = 0
    medium_items: int = 0
    low_items: int = 0

    # Categorized items
    items: List[RemediationItem] = field(default_factory=list)

    # Gaps by framework
    gaps_by_framework: Dict[str, List[RemediationItem]] = field(default_factory=dict)

    # Missing policies
    missing_policies: List[str] = field(default_factory=list)

    # Reference issues
    reference_issues: List[Dict[str, str]] = field(default_factory=list)


class RemediationReporter:
    """
    Generates comprehensive remediation reports

    These reports are a premium deliverable showing:
    - All policies out of compliance
    - Missing required policies
    - Incomplete sections requiring customization
    - Cross-reference issues
    - Recommended next steps
    """

    def __init__(self):
        pass

    def generate_report(self,
                       client_id: str,
                       client_name: str,
                       target_frameworks: List[str],
                       generated_policies: List[str],
                       incomplete_sections: List,
                       reference_issues: List,
                       gap_analysis: List) -> RemediationReport:
        """
        Generate a complete remediation report

        Args:
            client_id: Client identifier
            client_name: Client display name
            target_frameworks: Target compliance frameworks
            generated_policies: List of generated policy IDs
            incomplete_sections: List of IncompleteSection objects
            reference_issues: List of ReferenceIssue objects
            gap_analysis: List of Gap objects

        Returns:
            Complete RemediationReport
        """
        report = RemediationReport(
            client_id=client_id,
            client_name=client_name,
            generated_at=datetime.now().isoformat(),
            target_frameworks=target_frameworks,
            policies_generated=len(generated_policies)
        )

        # Process incomplete sections
        for section in incomplete_sections:
            item = RemediationItem(
                id=f"INC-{len(report.items)+1:04d}",
                category='incomplete_section',
                priority=section.priority,
                policy_id=section.policy_id,
                framework=section.frameworks[0] if section.frameworks else None,
                description=section.reason,
                remediation=f"Complete section {section.section} with required details",
                estimated_effort=self._estimate_effort('incomplete_section', section.priority)
            )
            report.items.append(item)
            report.policies_requiring_customization += 1

        # Process reference issues
        for issue in reference_issues:
            item = RemediationItem(
                id=f"REF-{len(report.items)+1:04d}",
                category='broken_reference',
                priority='high' if issue.status.value == 'broken' else 'medium',
                policy_id=issue.source_policy,
                framework=None,
                description=issue.message,
                remediation=f"Add missing policy '{issue.referenced_policy}' or update reference",
                estimated_effort=self._estimate_effort('broken_reference', 'high')
            )
            report.items.append(item)
            report.reference_issues.append({
                'source': issue.source_policy,
                'target': issue.referenced_policy,
                'status': issue.status.value
            })

        # Process gap analysis
        for gap in gap_analysis:
            for missing in gap.missing_policies:
                report.missing_policies.append(missing)
                item = RemediationItem(
                    id=f"GAP-{len(report.items)+1:04d}",
                    category='policy_gap',
                    priority=gap.severity,
                    policy_id=None,
                    framework=gap.framework_id,
                    description=f"Missing policy: {missing} (required for {gap.control_id})",
                    remediation=f"Create or acquire policy: {missing}",
                    estimated_effort=self._estimate_effort('policy_gap', gap.severity)
                )
                report.items.append(item)

                # Add to framework-specific gaps
                if gap.framework_id not in report.gaps_by_framework:
                    report.gaps_by_framework[gap.framework_id] = []
                report.gaps_by_framework[gap.framework_id].append(item)

        # Count by priority
        for item in report.items:
            if item.priority == 'critical':
                report.critical_items += 1
            elif item.priority == 'high':
                report.high_items += 1
            elif item.priority == 'medium':
                report.medium_items += 1
            else:
                report.low_items += 1

        return report

    def _estimate_effort(self, category: str, priority: str) -> str:
        """Estimate effort for remediation"""
        estimates = {
            ('incomplete_section', 'critical'): '2-4 hours',
            ('incomplete_section', 'high'): '1-2 hours',
            ('incomplete_section', 'medium'): '30-60 minutes',
            ('incomplete_section', 'low'): '15-30 minutes',
            ('broken_reference', 'high'): '1-2 hours',
            ('broken_reference', 'medium'): '30 minutes',
            ('policy_gap', 'critical'): '4-8 hours',
            ('policy_gap', 'high'): '2-4 hours',
            ('policy_gap', 'medium'): '1-2 hours',
        }
        return estimates.get((category, priority), '1 hour')

    def to_markdown(self, report: RemediationReport) -> str:
        """Convert report to markdown format"""
        lines = [
            f"# Compliance Remediation Report",
            f"## Client: {report.client_name}",
            f"## Assessment Date: {report.generated_at[:10]}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Total Policies Generated:** {report.policies_generated}",
            f"- **Policies Requiring Customization:** {report.policies_requiring_customization}",
            f"- **Critical Actions Required:** {report.critical_items}",
            f"- **High Priority Items:** {report.high_items}",
            f"- **Medium Priority Items:** {report.medium_items}",
            f"- **Low Priority Items:** {report.low_items}",
            f"- **Target Frameworks:** {', '.join(report.target_frameworks)}",
            "",
            "---",
            "",
            "## Remediation Items",
            "",
            "| ID | Priority | Category | Policy | Description | Remediation | Effort |",
            "|-----|----------|----------|--------|-------------|-------------|--------|",
        ]

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_items = sorted(report.items, key=lambda x: priority_order.get(x.priority, 4))

        for item in sorted_items:
            policy = item.policy_id or '-'
            lines.append(
                f"| {item.id} | {item.priority.upper()} | {item.category} | "
                f"{policy} | {item.description[:50]}... | {item.remediation[:40]}... | {item.estimated_effort} |"
            )

        # Add framework-specific sections
        if report.gaps_by_framework:
            lines.extend(["", "---", "", "## Gaps by Framework", ""])
            for framework, gaps in report.gaps_by_framework.items():
                lines.append(f"### {framework.upper()}")
                lines.append("")
                for gap in gaps:
                    lines.append(f"- [ ] {gap.description}")
                lines.append("")

        # Add missing policies section
        if report.missing_policies:
            lines.extend(["", "---", "", "## Missing Policies", ""])
            lines.append("The following policies need to be created:")
            lines.append("")
            for policy in sorted(set(report.missing_policies)):
                lines.append(f"- [ ] {policy}")

        # Add reference issues
        if report.reference_issues:
            lines.extend(["", "---", "", "## Reference Issues", ""])
            for issue in report.reference_issues:
                lines.append(f"- Policy `{issue['source']}` references missing `{issue['target']}`")

        # Add next steps
        lines.extend([
            "",
            "---",
            "",
            "## Recommended Next Steps",
            "",
            "1. Complete all CRITICAL priority items immediately",
            "2. Address HIGH priority items within 2 weeks",
            "3. Schedule MEDIUM priority items for completion within 30 days",
            "4. Review and approve all policies with stakeholders",
            "5. Distribute policies to all personnel",
            "6. Schedule annual policy review",
            "",
            "---",
            "",
            f"*Report generated by PolicyUpdate GRC Platform*"
        ])

        return '\n'.join(lines)
