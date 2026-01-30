"""
Compliance Mapper Module
Maps policies to compliance framework controls

Supports multiple framework structures:
- NIST CSF 2.0: functions → categories → subcategories
- SOC 2: categories → criteria
- ISO 27001: themes → controls
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Any


@dataclass
class Control:
    """A compliance framework control"""
    id: str
    name: str
    description: str
    policies_required: List[str] = field(default_factory=list)
    policies_recommended: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    parent_category: str = ""
    parent_function: str = ""


@dataclass
class Framework:
    """A compliance framework definition"""
    id: str
    name: str
    version: str
    release_date: str = ""
    authority: str = ""
    url: str = ""
    controls: Dict[str, Control] = field(default_factory=dict)

    @property
    def total_controls(self) -> int:
        return len(self.controls)

    def get_all_required_policies(self) -> Set[str]:
        """Get all unique policies required by this framework"""
        policies = set()
        for control in self.controls.values():
            policies.update(control.policies_required)
        return policies

    def get_all_recommended_policies(self) -> Set[str]:
        """Get all unique policies recommended by this framework"""
        policies = set()
        for control in self.controls.values():
            policies.update(control.policies_recommended)
        return policies


class ComplianceMapper:
    """Maps policies to compliance framework controls"""

    def __init__(self, frameworks_dir: Optional[str] = None):
        self.frameworks: Dict[str, Framework] = {}
        self.policy_mapping: Dict[str, Dict[str, List[str]]] = {}
        self._frameworks_dir = Path(frameworks_dir) if frameworks_dir else None

    def load_framework(self, filepath: str) -> Framework:
        """Load a framework definition from YAML"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Framework file not found: {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Extract framework metadata
        fw_data = data.get('framework', {})
        framework = Framework(
            id=fw_data.get('id', path.stem),
            name=fw_data.get('name', ''),
            version=str(fw_data.get('version', '')),
            release_date=str(fw_data.get('release_date', '')),
            authority=fw_data.get('authority', ''),
            url=fw_data.get('url', '')
        )

        # Parse controls based on framework structure
        if 'functions' in data:
            # NIST CSF 2.0 structure: functions → categories → subcategories
            self._parse_nist_csf_structure(framework, data['functions'])
        elif 'categories' in data:
            # SOC 2 structure: categories → criteria
            self._parse_soc2_structure(framework, data['categories'])
        elif 'themes' in data:
            # ISO 27001 structure: themes → controls
            self._parse_iso27001_structure(framework, data['themes'])
        elif 'safeguards' in data:
            # HIPAA structure: safeguards → controls
            self._parse_hipaa_structure(framework, data['safeguards'])
        elif 'requirements' in data:
            # PCI DSS structure: requirements → controls
            self._parse_pci_structure(framework, data['requirements'])
        elif 'chapters' in data:
            # GDPR structure: chapters → controls
            self._parse_gdpr_structure(framework, data['chapters'])
        elif 'families' in data:
            # NIST 800-171 structure: families → controls
            self._parse_families_structure(framework, data['families'])
        elif 'sections' in data:
            # CCPA structure: sections → controls
            self._parse_sections_structure(framework, data['sections'])
        elif 'articles' in fw_data:
            # NIS2/EU AI Act structure: articles → controls
            self._parse_articles_structure(framework, fw_data['articles'])
        else:
            raise ValueError(f"Unknown framework structure in {filepath}")

        # Store framework and build reverse mapping
        self.frameworks[framework.id] = framework
        self._build_policy_mapping(framework)

        return framework

    def _parse_nist_csf_structure(self, framework: Framework, functions: Dict) -> None:
        """Parse NIST CSF 2.0 structure (functions → categories → subcategories)"""
        for func_id, func_data in functions.items():
            func_name = func_data.get('name', str(func_id))

            for cat_id, cat_data in func_data.get('categories', {}).items():
                cat_name = cat_data.get('name', str(cat_id))

                for subcat_id, subcat_data in cat_data.get('subcategories', {}).items():
                    subcat_id_str = str(subcat_id)
                    control = Control(
                        id=subcat_id_str,
                        name=subcat_data.get('name', subcat_id_str),
                        description=subcat_data.get('description', ''),
                        policies_required=subcat_data.get('policies_required', []) or [],
                        policies_recommended=subcat_data.get('policies_recommended', []) or [],
                        evidence_types=subcat_data.get('evidence_types', []) or [],
                        parent_category=cat_name,
                        parent_function=func_name
                    )
                    framework.controls[subcat_id_str] = control

    def _parse_soc2_structure(self, framework: Framework, categories: Dict) -> None:
        """Parse SOC 2 structure (categories → criteria)"""
        for cat_id, cat_data in categories.items():
            cat_name = cat_data.get('name', str(cat_id))

            for crit_id, crit_data in cat_data.get('criteria', {}).items():
                crit_id_str = str(crit_id)
                control = Control(
                    id=crit_id_str,
                    name=crit_data.get('name', crit_id_str),
                    description=crit_data.get('description', ''),
                    policies_required=crit_data.get('policies_required', []) or [],
                    policies_recommended=crit_data.get('policies_recommended', []) or [],
                    evidence_types=crit_data.get('evidence_types', []) or [],
                    parent_category=cat_name,
                    parent_function=""
                )
                framework.controls[crit_id_str] = control

    def _parse_iso27001_structure(self, framework: Framework, themes: Dict) -> None:
        """Parse ISO 27001 structure (themes → controls)"""
        for theme_id, theme_data in themes.items():
            theme_name = theme_data.get('name', str(theme_id))

            for ctrl_id, ctrl_data in theme_data.get('controls', {}).items():
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=theme_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_hipaa_structure(self, framework: Framework, safeguards: Dict) -> None:
        """Parse HIPAA structure (safeguards → controls)"""
        for safeguard_id, safeguard_data in safeguards.items():
            safeguard_name = safeguard_data.get('name', safeguard_id)

            for ctrl_id, ctrl_data in safeguard_data.get('controls', {}).items():
                # Ensure control ID is a string (YAML may parse numeric-looking IDs as floats)
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=safeguard_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_pci_structure(self, framework: Framework, requirements: Dict) -> None:
        """Parse PCI DSS structure (requirements → controls)"""
        for req_id, req_data in requirements.items():
            req_name = req_data.get('name', str(req_id))

            for ctrl_id, ctrl_data in req_data.get('controls', {}).items():
                # Ensure control ID is a string (PCI uses numeric IDs like "1.1", "1.2")
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=req_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_gdpr_structure(self, framework: Framework, chapters: Dict) -> None:
        """Parse GDPR structure (chapters → controls)"""
        for chapter_id, chapter_data in chapters.items():
            chapter_name = chapter_data.get('name', str(chapter_id))

            for ctrl_id, ctrl_data in chapter_data.get('controls', {}).items():
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=chapter_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_families_structure(self, framework: Framework, families: Dict) -> None:
        """Parse NIST 800-171 structure (families → controls)"""
        for family_id, family_data in families.items():
            family_name = family_data.get('name', str(family_id))

            for ctrl_id, ctrl_data in family_data.get('controls', {}).items():
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=family_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_sections_structure(self, framework: Framework, sections: Dict) -> None:
        """Parse CCPA structure (sections → controls)"""
        for section_id, section_data in sections.items():
            section_name = section_data.get('name', str(section_id))

            for ctrl_id, ctrl_data in section_data.get('controls', {}).items():
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=section_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _parse_articles_structure(self, framework: Framework, articles: Dict) -> None:
        """Parse NIS2/EU AI Act structure (articles → controls)"""
        for article_id, article_data in articles.items():
            article_name = article_data.get('name', str(article_id))

            for ctrl_id, ctrl_data in article_data.get('controls', {}).items():
                ctrl_id_str = str(ctrl_id)
                control = Control(
                    id=ctrl_id_str,
                    name=ctrl_data.get('name', ctrl_id_str),
                    description=ctrl_data.get('description', ''),
                    policies_required=ctrl_data.get('policies_required', []) or [],
                    policies_recommended=ctrl_data.get('policies_recommended', []) or [],
                    evidence_types=ctrl_data.get('evidence_types', []) or [],
                    parent_category=article_name,
                    parent_function=""
                )
                framework.controls[ctrl_id_str] = control

    def _build_policy_mapping(self, framework: Framework) -> None:
        """Build reverse mapping from policies to framework controls"""
        for control in framework.controls.values():
            for policy_id in control.policies_required:
                if policy_id not in self.policy_mapping:
                    self.policy_mapping[policy_id] = {}
                if framework.id not in self.policy_mapping[policy_id]:
                    self.policy_mapping[policy_id][framework.id] = []
                self.policy_mapping[policy_id][framework.id].append(control.id)

            for policy_id in control.policies_recommended:
                if policy_id not in self.policy_mapping:
                    self.policy_mapping[policy_id] = {}
                if framework.id not in self.policy_mapping[policy_id]:
                    self.policy_mapping[policy_id][framework.id] = []
                # Mark as recommended with suffix
                if control.id not in self.policy_mapping[policy_id][framework.id]:
                    self.policy_mapping[policy_id][framework.id].append(f"{control.id}*")

    def load_all_frameworks(self, frameworks_dir: Optional[str] = None) -> Dict[str, Framework]:
        """Load all framework YAML files from a directory"""
        dir_path = Path(frameworks_dir) if frameworks_dir else self._frameworks_dir
        if not dir_path or not dir_path.exists():
            raise FileNotFoundError(f"Frameworks directory not found: {dir_path}")

        for yaml_file in dir_path.glob("*.yaml"):
            try:
                self.load_framework(str(yaml_file))
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file.name}: {e}")

        return self.frameworks

    def get_required_policies(self, framework_id: str) -> List[str]:
        """Get all policies required for a framework"""
        framework = self.frameworks.get(framework_id)
        if not framework:
            return []
        return sorted(framework.get_all_required_policies())

    def get_recommended_policies(self, framework_id: str) -> List[str]:
        """Get all policies recommended for a framework"""
        framework = self.frameworks.get(framework_id)
        if not framework:
            return []
        return sorted(framework.get_all_recommended_policies())

    def get_policy_frameworks(self, policy_id: str) -> Dict[str, List[str]]:
        """Get frameworks and controls satisfied by a policy"""
        return self.policy_mapping.get(policy_id, {})

    def get_controls_for_policy(self, policy_id: str, framework_id: Optional[str] = None) -> List[str]:
        """Get specific controls satisfied by a policy"""
        mapping = self.policy_mapping.get(policy_id, {})
        if framework_id:
            return mapping.get(framework_id, [])

        # Return all controls across frameworks
        all_controls = []
        for fw_id, controls in mapping.items():
            all_controls.extend([f"{fw_id}:{ctrl}" for ctrl in controls])
        return all_controls

    def find_overlap(self, framework_ids: List[str]) -> Dict[str, Set[str]]:
        """Find policies that satisfy multiple frameworks"""
        if len(framework_ids) < 2:
            return {}

        # Get policies for each framework
        framework_policies = {}
        for fw_id in framework_ids:
            if fw_id in self.frameworks:
                framework_policies[fw_id] = self.frameworks[fw_id].get_all_required_policies()

        # Find overlapping policies
        overlap = {}
        all_policies = set()
        for policies in framework_policies.values():
            all_policies.update(policies)

        for policy_id in all_policies:
            frameworks_using = set()
            for fw_id, policies in framework_policies.items():
                if policy_id in policies:
                    frameworks_using.add(fw_id)

            if len(frameworks_using) >= 2:
                overlap[policy_id] = frameworks_using

        return overlap

    def get_coverage_report(self, available_policies: List[str], framework_id: str) -> Dict[str, Any]:
        """Generate a coverage report for a framework given available policies"""
        framework = self.frameworks.get(framework_id)
        if not framework:
            return {"error": f"Framework not found: {framework_id}"}

        required_policies = framework.get_all_required_policies()
        available_set = set(available_policies)

        covered = required_policies & available_set
        missing = required_policies - available_set

        # Calculate control coverage
        controls_fully_covered = 0
        controls_partially_covered = 0
        controls_not_covered = 0

        control_details = {}
        for ctrl_id, control in framework.controls.items():
            required = set(control.policies_required)
            has = required & available_set

            if len(required) == 0:
                controls_fully_covered += 1
                control_details[ctrl_id] = "no_requirements"
            elif has == required:
                controls_fully_covered += 1
                control_details[ctrl_id] = "fully_covered"
            elif len(has) > 0:
                controls_partially_covered += 1
                control_details[ctrl_id] = f"partial ({len(has)}/{len(required)})"
            else:
                controls_not_covered += 1
                control_details[ctrl_id] = "not_covered"

        return {
            "framework_id": framework_id,
            "framework_name": framework.name,
            "total_controls": framework.total_controls,
            "controls_fully_covered": controls_fully_covered,
            "controls_partially_covered": controls_partially_covered,
            "controls_not_covered": controls_not_covered,
            "coverage_percentage": round(
                (controls_fully_covered / framework.total_controls) * 100, 1
            ) if framework.total_controls > 0 else 0,
            "required_policies_total": len(required_policies),
            "required_policies_available": len(covered),
            "required_policies_missing": len(missing),
            "missing_policies": sorted(missing),
            "control_details": control_details
        }

    def get_framework_summary(self, framework_id: str) -> Dict[str, Any]:
        """Get summary information about a framework"""
        framework = self.frameworks.get(framework_id)
        if not framework:
            return {"error": f"Framework not found: {framework_id}"}

        return {
            "id": framework.id,
            "name": framework.name,
            "version": framework.version,
            "authority": framework.authority,
            "total_controls": framework.total_controls,
            "required_policies": len(framework.get_all_required_policies()),
            "recommended_policies": len(framework.get_all_recommended_policies())
        }

    def generate_policy_framework_matrix(self,
                                         policy_ids: List[str],
                                         framework_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, List[str]]]:
        """Generate a matrix showing which policies map to which framework controls"""
        if framework_ids is None:
            framework_ids = list(self.frameworks.keys())

        matrix = {}
        for policy_id in policy_ids:
            matrix[policy_id] = {}
            mapping = self.policy_mapping.get(policy_id, {})
            for fw_id in framework_ids:
                matrix[policy_id][fw_id] = mapping.get(fw_id, [])

        return matrix


def main():
    """Test the compliance mapper"""
    import sys

    # Find frameworks directory
    script_dir = Path(__file__).parent
    frameworks_dir = script_dir.parent.parent / "config" / "frameworks"

    if not frameworks_dir.exists():
        print(f"Frameworks directory not found: {frameworks_dir}")
        sys.exit(1)

    print(f"Loading frameworks from: {frameworks_dir}")
    print("=" * 60)

    mapper = ComplianceMapper()
    mapper.load_all_frameworks(str(frameworks_dir))

    print(f"\nLoaded {len(mapper.frameworks)} frameworks:")
    for fw_id, framework in mapper.frameworks.items():
        print(f"\n  {fw_id}:")
        summary = mapper.get_framework_summary(fw_id)
        print(f"    Name: {summary['name']}")
        print(f"    Version: {summary['version']}")
        print(f"    Total Controls: {summary['total_controls']}")
        print(f"    Required Policies: {summary['required_policies']}")
        print(f"    Recommended Policies: {summary['recommended_policies']}")

    print("\n" + "=" * 60)
    print("Policy Mapping Examples:")

    # Show some example policy mappings
    example_policies = [
        "access-control-policy",
        "incident-response-policy",
        "risk-management-policy",
        "information-security-policy"
    ]

    for policy_id in example_policies:
        mapping = mapper.get_policy_frameworks(policy_id)
        if mapping:
            print(f"\n  {policy_id}:")
            for fw_id, controls in mapping.items():
                print(f"    {fw_id}: {', '.join(controls[:5])}{'...' if len(controls) > 5 else ''}")

    print("\n" + "=" * 60)
    print("Framework Overlap Analysis:")

    overlap = mapper.find_overlap(list(mapper.frameworks.keys()))
    print(f"\n  Policies satisfying multiple frameworks: {len(overlap)}")

    # Show top 10 most overlapping policies
    sorted_overlap = sorted(overlap.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for policy_id, frameworks in sorted_overlap:
        print(f"    {policy_id}: {len(frameworks)} frameworks")


if __name__ == "__main__":
    main()
