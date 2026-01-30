"""
Package Builder Module
Builds complete policy packages for clients
"""

import yaml
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime


@dataclass
class ClientConfig:
    """Client configuration for policy generation"""
    name: str
    variables: Dict[str, str] = field(default_factory=dict)
    frameworks: List[str] = field(default_factory=list)
    industry: str = ""
    size_tier: str = "medium"  # solopreneur, small, medium, enterprise


@dataclass
class PolicyDocument:
    """A rendered policy document"""
    id: str
    title: str
    content: str
    category: str
    frameworks: Dict[str, List[str]]
    variables_used: List[str]
    incomplete_sections: List[Dict[str, Any]]


@dataclass
class PackageResult:
    """Result of building a policy package"""
    client_name: str
    generated_at: datetime
    policies: List[PolicyDocument]
    total_policies: int
    frameworks_covered: List[str]
    variables_applied: Dict[str, str]
    incomplete_count: int
    warnings: List[str]


class PackageBuilder:
    """
    Builds complete policy packages for clients.

    Usage:
        builder = PackageBuilder(policies_dir, frameworks_dir)
        config = ClientConfig(
            name="Acme Corp",
            variables={"ORGANIZATION_NAME": "Acme Corporation"},
            frameworks=["soc2", "hipaa"]
        )
        result = builder.build_package(config)
    """

    def __init__(self, policies_dir: str, frameworks_dir: Optional[str] = None):
        self.policies_dir = Path(policies_dir)
        self.frameworks_dir = Path(frameworks_dir) if frameworks_dir else None
        self.policies_cache: Dict[str, Dict] = {}
        self.compliance_mapper = None

        if self.frameworks_dir:
            self._init_compliance_mapper()

    def _init_compliance_mapper(self):
        """Initialize compliance mapper if frameworks directory exists"""
        try:
            import sys
            sys.path.insert(0, str(self.policies_dir.parent / "src"))
            from core.compliance_mapper import ComplianceMapper

            self.compliance_mapper = ComplianceMapper()
            self.compliance_mapper.load_all_frameworks(str(self.frameworks_dir))
        except Exception as e:
            print(f"Warning: Could not initialize compliance mapper: {e}")

    def load_policy(self, policy_path: Path) -> Optional[Dict]:
        """Load a policy file and parse its frontmatter and content"""
        if str(policy_path) in self.policies_cache:
            return self.policies_cache[str(policy_path)]

        try:
            content = policy_path.read_text(encoding='utf-8')

            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()

            policy_data = {
                'path': str(policy_path),
                'frontmatter': frontmatter,
                'body': body,
                'id': frontmatter.get('id', policy_path.stem),
                'title': frontmatter.get('title', ''),
                'category': frontmatter.get('category', ''),
                'frameworks': frontmatter.get('frameworks', {}),
                'variables': frontmatter.get('variables', []),
                'requires_customization': frontmatter.get('requires_customization', [])
            }

            self.policies_cache[str(policy_path)] = policy_data
            return policy_data

        except Exception as e:
            print(f"Warning: Could not load policy {policy_path}: {e}")
            return None

    def get_all_policies(self) -> Dict[str, Dict]:
        """Load all policies from the policies directory"""
        policies = {}
        for md_file in self.policies_dir.rglob("*.md"):
            policy = self.load_policy(md_file)
            if policy:
                policies[policy['id']] = policy
        return policies

    def get_policies_for_frameworks(self, framework_ids: List[str]) -> Set[str]:
        """Get policy IDs required for specified frameworks"""
        if not self.compliance_mapper:
            return set()

        required_policies = set()
        for fw_id in framework_ids:
            policies = self.compliance_mapper.get_required_policies(fw_id)
            required_policies.update(policies)

        return required_policies

    def apply_variables(self, content: str, variables: Dict[str, str]) -> str:
        """Apply variable substitution to content"""
        result = content
        for var_name, var_value in variables.items():
            # Replace {{VARIABLE_NAME}} syntax
            pattern = r'\{\{' + var_name + r'\}\}'
            result = re.sub(pattern, var_value, result)
        return result

    def detect_incomplete_sections(self, content: str, policy_id: str) -> List[Dict[str, Any]]:
        """Detect sections that require customization"""
        incomplete = []

        # Find unreplaced variables
        unreplaced = re.findall(r'\{\{([A-Z_]+)\}\}', content)
        if unreplaced:
            incomplete.append({
                'type': 'unreplaced_variables',
                'variables': list(set(unreplaced)),
                'severity': 'high'
            })

        # Find ACTION REQUIRED markers
        action_markers = re.findall(r'\[ACTION REQUIRED[^\]]*\]', content, re.IGNORECASE)
        if action_markers:
            incomplete.append({
                'type': 'action_required',
                'markers': action_markers,
                'severity': 'high'
            })

        # Find TODO markers
        todo_markers = re.findall(r'\[TODO[^\]]*\]', content, re.IGNORECASE)
        if todo_markers:
            incomplete.append({
                'type': 'todo',
                'markers': todo_markers,
                'severity': 'medium'
            })

        return incomplete

    def render_policy(self, policy: Dict, variables: Dict[str, str]) -> PolicyDocument:
        """Render a single policy with variable substitution"""
        # Apply variables to content
        rendered_content = self.apply_variables(policy['body'], variables)

        # Apply variables to title
        rendered_title = self.apply_variables(policy['title'], variables)

        # Detect incomplete sections
        incomplete = self.detect_incomplete_sections(rendered_content, policy['id'])

        return PolicyDocument(
            id=policy['id'],
            title=rendered_title,
            content=rendered_content,
            category=policy['category'],
            frameworks=policy.get('frameworks', {}),
            variables_used=policy.get('variables', []),
            incomplete_sections=incomplete
        )

    def build_package(self, config: ClientConfig,
                      include_all: bool = False,
                      validate_references: bool = True) -> PackageResult:
        """
        Build a complete policy package for a client.

        Args:
            config: Client configuration
            include_all: Include all policies regardless of framework mapping
            validate_references: Check cross-references between policies

        Returns:
            PackageResult with rendered policies and metadata
        """
        warnings = []
        all_policies = self.get_all_policies()

        # Determine which policies to include
        if include_all:
            policy_ids = set(all_policies.keys())
        elif config.frameworks:
            policy_ids = self.get_policies_for_frameworks(config.frameworks)
            # Also get policies that have framework mappings
            for policy_id, policy in all_policies.items():
                for fw_id in config.frameworks:
                    if fw_id in policy.get('frameworks', {}):
                        policy_ids.add(policy_id)
        else:
            policy_ids = set(all_policies.keys())

        # Build default variables
        default_variables = {
            'ORGANIZATION_NAME': config.name,
            'EFFECTIVE_DATE': datetime.now().strftime('%B %d, %Y'),
            'APPROVAL_DATE': datetime.now().strftime('%B %d, %Y'),
            'VERSION': '1.0.0'
        }

        # Merge with client-provided variables
        variables = {**default_variables, **config.variables}

        # Render policies
        rendered_policies = []
        incomplete_count = 0

        for policy_id in sorted(policy_ids):
            if policy_id not in all_policies:
                warnings.append(f"Policy not found: {policy_id}")
                continue

            policy = all_policies[policy_id]
            rendered = self.render_policy(policy, variables)
            rendered_policies.append(rendered)

            if rendered.incomplete_sections:
                incomplete_count += 1

        # Validate cross-references if enabled
        if validate_references:
            for policy in rendered_policies:
                refs = all_policies.get(policy.id, {}).get('frontmatter', {}).get('references', [])
                for ref in refs:
                    if ref not in policy_ids and ref not in all_policies:
                        warnings.append(f"Policy '{policy.id}' references missing policy: {ref}")

        return PackageResult(
            client_name=config.name,
            generated_at=datetime.now(),
            policies=rendered_policies,
            total_policies=len(rendered_policies),
            frameworks_covered=config.frameworks,
            variables_applied=variables,
            incomplete_count=incomplete_count,
            warnings=warnings
        )

    def generate_table_of_contents(self, result: PackageResult) -> str:
        """Generate a table of contents for the package"""
        lines = [
            f"# {result.client_name} - Policy Package",
            f"",
            f"**Generated:** {result.generated_at.strftime('%B %d, %Y')}",
            f"**Total Policies:** {result.total_policies}",
            f"**Frameworks:** {', '.join(result.frameworks_covered) or 'All'}",
            f"",
            "---",
            "",
            "## Table of Contents",
            ""
        ]

        # Group by category
        categories = {}
        for policy in result.policies:
            cat = policy.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(policy)

        for category in sorted(categories.keys()):
            lines.append(f"### {category.replace('-', ' ').title()}")
            for policy in sorted(categories[category], key=lambda p: p.title):
                status = "⚠️" if policy.incomplete_sections else "✅"
                lines.append(f"- {status} {policy.title}")
            lines.append("")

        if result.incomplete_count > 0:
            lines.extend([
                "---",
                "",
                f"**⚠️ {result.incomplete_count} policies require customization**",
                ""
            ])

        return "\n".join(lines)

    def generate_customization_checklist(self, result: PackageResult) -> str:
        """Generate a checklist of required customizations"""
        lines = [
            f"# Policy Customization Checklist",
            f"## {result.client_name}",
            f"",
            f"**Generated:** {result.generated_at.strftime('%B %d, %Y')}",
            f"",
            "---",
            "",
        ]

        has_items = False
        for policy in result.policies:
            if not policy.incomplete_sections:
                continue

            has_items = True
            lines.append(f"### {policy.title}")
            lines.append(f"**Policy ID:** {policy.id}")
            lines.append("")

            for item in policy.incomplete_sections:
                if item['type'] == 'unreplaced_variables':
                    lines.append("**Unreplaced Variables:**")
                    for var in item['variables']:
                        lines.append(f"- [ ] Set value for `{{{{{var}}}}}`")

                elif item['type'] == 'action_required':
                    lines.append("**Action Required:**")
                    for marker in item['markers']:
                        lines.append(f"- [ ] {marker}")

                elif item['type'] == 'todo':
                    lines.append("**To Do:**")
                    for marker in item['markers']:
                        lines.append(f"- [ ] {marker}")

            lines.append("")

        if not has_items:
            lines.append("✅ **No customizations required!**")
            lines.append("")
            lines.append("All policies have been fully populated with the provided variables.")

        return "\n".join(lines)


def main():
    """Test the package builder"""
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    policies_dir = project_root / "policies"
    frameworks_dir = project_root / "config" / "frameworks"

    print("=" * 70)
    print("PACKAGE BUILDER TEST")
    print("=" * 70)

    builder = PackageBuilder(str(policies_dir), str(frameworks_dir))

    # Test with sample client
    config = ClientConfig(
        name="Acme Corporation",
        variables={
            "ORGANIZATION_NAME": "Acme Corporation",
            "CSO_TITLE": "Chief Information Security Officer",
            "EXEC_MGMT": "Executive Leadership Team",
            "IT_STAFF": "IT Department",
            "HR_DEPARTMENT": "Human Resources",
            "LEGAL_DEPARTMENT": "Legal Department",
            "RMO_TITLE": "Risk Management Officer"
        },
        frameworks=["soc2", "hipaa"]
    )

    print(f"\nBuilding package for: {config.name}")
    print(f"Frameworks: {config.frameworks}")
    print("-" * 50)

    result = builder.build_package(config)

    print(f"\nPackage Summary:")
    print(f"  Total Policies: {result.total_policies}")
    print(f"  Incomplete: {result.incomplete_count}")
    print(f"  Warnings: {len(result.warnings)}")

    if result.warnings:
        print(f"\nWarnings:")
        for w in result.warnings[:5]:
            print(f"  - {w}")

    # Generate TOC
    toc = builder.generate_table_of_contents(result)
    print(f"\n{'-' * 50}")
    print("Table of Contents Preview:")
    print("-" * 50)
    print(toc[:1000] + "..." if len(toc) > 1000 else toc)


if __name__ == "__main__":
    main()
