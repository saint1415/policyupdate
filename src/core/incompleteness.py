"""
Incompleteness Detection Module
Detects sections requiring customization for specific compliance requirements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class IncompleteSection:
    """A section requiring customization"""
    policy_id: str
    section: str
    reason: str
    frameworks: List[str]
    priority: str = "medium"  # low, medium, high, critical
    suggested_content: Optional[str] = None


class IncompletenessDetector:
    """
    Detects incomplete sections in policies
    Identifies areas requiring client-specific customization
    """

    # Patterns that indicate incomplete sections
    INCOMPLETE_PATTERNS = [
        (r'\[.*?REQUIRED.*?\]', 'high'),
        (r'\[.*?TODO.*?\]', 'medium'),
        (r'\[.*?INSERT.*?\]', 'medium'),
        (r'\[.*?SPECIFY.*?\]', 'medium'),
        (r'<.*?>', 'low'),  # Placeholder brackets
        (r'X{2,}', 'low'),  # XXX placeholders
    ]

    # Framework-specific requirements that need detail
    FRAMEWORK_REQUIREMENTS = {
        'pci_dss': [
            {'pattern': r'cardholder data environment', 'required': 'CDE IP ranges and network diagram'},
            {'pattern': r'encryption', 'required': 'Specific encryption algorithms and key lengths'},
            {'pattern': r'payment channel', 'required': 'List of payment channels and processors'},
        ],
        'hipaa': [
            {'pattern': r'privacy officer', 'required': 'Named Privacy Officer'},
            {'pattern': r'protected health information', 'required': 'PHI handling procedures'},
            {'pattern': r'business associate', 'required': 'List of business associates'},
        ],
        'gdpr': [
            {'pattern': r'data protection officer', 'required': 'Named DPO'},
            {'pattern': r'lawful basis', 'required': 'Documented lawful basis for processing'},
            {'pattern': r'data subject rights', 'required': 'Specific procedures for each right'},
        ],
        'soc2': [
            {'pattern': r'monitoring', 'required': 'Specific monitoring tools and thresholds'},
            {'pattern': r'incident', 'required': 'Incident classification criteria'},
        ]
    }

    def __init__(self):
        pass

    def detect(self, policy_id: str, content: str,
               target_frameworks: List[str] = None) -> List[IncompleteSection]:
        """
        Detect incomplete sections in a policy

        Args:
            policy_id: ID of the policy
            content: Policy content to analyze
            target_frameworks: Frameworks to check requirements for

        Returns:
            List of incomplete sections
        """
        incomplete = []

        # Check generic patterns
        for pattern, priority in self.INCOMPLETE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                incomplete.append(IncompleteSection(
                    policy_id=policy_id,
                    section=self._find_section(content, match.start()),
                    reason=f"Contains placeholder: {match.group()}",
                    frameworks=[],
                    priority=priority
                ))

        # Check framework-specific requirements
        if target_frameworks:
            for framework in target_frameworks:
                if framework in self.FRAMEWORK_REQUIREMENTS:
                    for req in self.FRAMEWORK_REQUIREMENTS[framework]:
                        if re.search(req['pattern'], content, re.IGNORECASE):
                            incomplete.append(IncompleteSection(
                                policy_id=policy_id,
                                section=self._find_section_by_pattern(content, req['pattern']),
                                reason=f"{framework.upper()} requires: {req['required']}",
                                frameworks=[framework],
                                priority='high'
                            ))

        return incomplete

    def _find_section(self, content: str, position: int) -> str:
        """Find the section containing a position"""
        # Look backwards for nearest heading
        before = content[:position]
        heading_match = re.findall(r'^(#{1,6}|[IVX]+\.|[A-Z]\.).*$', before, re.MULTILINE)
        if heading_match:
            return heading_match[-1][:50]
        return "Unknown section"

    def _find_section_by_pattern(self, content: str, pattern: str) -> str:
        """Find section containing a pattern"""
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return self._find_section(content, match.start())
        return "Unknown section"

    def generate_checklist(self, incomplete_sections: List[IncompleteSection]) -> str:
        """Generate a markdown checklist of required customizations"""
        lines = ["# Policy Customization Checklist", ""]
        lines.append("| Priority | Policy | Section | Requirement | Frameworks |")
        lines.append("|----------|--------|---------|-------------|------------|")

        for item in sorted(incomplete_sections, key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x.priority],
            x.policy_id
        )):
            frameworks = ', '.join(item.frameworks) if item.frameworks else '-'
            lines.append(
                f"| {item.priority.upper()} | {item.policy_id} | {item.section} | "
                f"{item.reason} | {frameworks} |"
            )

        return '\n'.join(lines)
