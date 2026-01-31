"""
OSCAL Export Module
Export policies and compliance data to OSCAL (Open Security Controls Assessment Language) format
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from core.config import get_logger
    logger = get_logger('generation.oscal')
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class OscalMetadata:
    """OSCAL document metadata"""
    title: str
    version: str
    oscal_version: str = "1.1.2"
    last_modified: str = None
    published: str = None

    def __post_init__(self):
        if self.last_modified is None:
            self.last_modified = datetime.now().isoformat()
        if self.published is None:
            self.published = datetime.now().isoformat()


class OscalExporter:
    """
    Exports policy packages to OSCAL format.

    Supports:
    - System Security Plan (SSP)
    - Component Definition
    - Assessment Plan
    - Assessment Results

    OSCAL is a NIST standard for machine-readable security documentation.
    """

    OSCAL_VERSION = "1.1.2"
    OSCAL_NS = "http://csrc.nist.gov/ns/oscal/1.0"

    def __init__(self):
        self.uuid_namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

    def _generate_uuid(self, name: str) -> str:
        """Generate deterministic UUID based on name"""
        return str(uuid.uuid5(self.uuid_namespace, name))

    def export_ssp(self, package_result, output_path: str,
                   system_name: str = None, system_description: str = None) -> str:
        """
        Export as OSCAL System Security Plan (SSP).

        The SSP is the primary document describing how a system implements
        security controls.

        Args:
            package_result: The PackageResult from generation
            output_path: Path to write JSON output
            system_name: Name of the system
            system_description: Description of the system

        Returns:
            Path to the created file
        """
        client_name = package_result.client_name
        system_name = system_name or f"{client_name} Information System"

        ssp = {
            "system-security-plan": {
                "uuid": self._generate_uuid(f"ssp-{client_name}"),
                "metadata": {
                    "title": f"System Security Plan - {client_name}",
                    "last-modified": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "oscal-version": self.OSCAL_VERSION,
                    "roles": [
                        {
                            "id": "system-owner",
                            "title": "System Owner"
                        },
                        {
                            "id": "authorizing-official",
                            "title": "Authorizing Official"
                        },
                        {
                            "id": "system-security-officer",
                            "title": "System Security Officer"
                        }
                    ],
                    "parties": [
                        {
                            "uuid": self._generate_uuid(f"party-{client_name}"),
                            "type": "organization",
                            "name": client_name
                        }
                    ]
                },
                "import-profile": {
                    "href": "#profile"
                },
                "system-characteristics": {
                    "system-ids": [
                        {
                            "id": self._generate_uuid(f"system-{client_name}"),
                            "identifier-type": "https://ietf.org/rfc/rfc4122"
                        }
                    ],
                    "system-name": system_name,
                    "description": system_description or f"Information system for {client_name}",
                    "security-sensitivity-level": "moderate",
                    "system-information": {
                        "information-types": [
                            {
                                "uuid": self._generate_uuid(f"info-type-{client_name}"),
                                "title": "Organizational Data",
                                "description": "Business and operational information",
                                "categorizations": [
                                    {
                                        "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                                        "information-type-ids": ["C.3.5.1"]
                                    }
                                ],
                                "confidentiality-impact": {"base": "moderate"},
                                "integrity-impact": {"base": "moderate"},
                                "availability-impact": {"base": "moderate"}
                            }
                        ]
                    },
                    "security-impact-level": {
                        "security-objective-confidentiality": "moderate",
                        "security-objective-integrity": "moderate",
                        "security-objective-availability": "moderate"
                    },
                    "status": {
                        "state": "operational"
                    },
                    "authorization-boundary": {
                        "description": f"The authorization boundary encompasses all {client_name} information systems and data."
                    }
                },
                "system-implementation": {
                    "users": [
                        {
                            "uuid": self._generate_uuid(f"user-admin-{client_name}"),
                            "role-ids": ["system-owner"],
                            "title": "System Administrator",
                            "props": [
                                {"name": "type", "value": "internal"}
                            ]
                        }
                    ],
                    "components": self._build_components(package_result)
                },
                "control-implementation": {
                    "description": f"Security control implementation for {client_name}",
                    "implemented-requirements": self._build_implemented_requirements(package_result)
                }
            }
        }

        # Write to file
        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(ssp, f, indent=2)

        logger.info(f"Exported OSCAL SSP to {output_path}")
        return str(output_path)

    def _build_components(self, package_result) -> List[Dict]:
        """Build OSCAL components from policies"""
        components = []

        # Create a component for the policy framework
        components.append({
            "uuid": self._generate_uuid(f"component-policies-{package_result.client_name}"),
            "type": "policy",
            "title": "Security Policy Framework",
            "description": f"Security policies for {package_result.client_name}",
            "status": {
                "state": "operational"
            },
            "props": [
                {"name": "policy-count", "value": str(package_result.total_policies)},
                {"name": "frameworks-covered", "value": ", ".join(package_result.frameworks_covered)}
            ]
        })

        # Group policies by category
        categories = {}
        for policy in package_result.policies:
            cat = policy.category or "general"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(policy)

        # Create component for each category
        for category, policies in categories.items():
            components.append({
                "uuid": self._generate_uuid(f"component-{category}-{package_result.client_name}"),
                "type": "policy",
                "title": f"{category.replace('-', ' ').title()} Policies",
                "description": f"Policies in the {category} category",
                "status": {"state": "operational"},
                "props": [
                    {"name": "policy-count", "value": str(len(policies))},
                    {"name": "category", "value": category}
                ]
            })

        return components

    def _build_implemented_requirements(self, package_result) -> List[Dict]:
        """Build OSCAL implemented requirements from policies"""
        requirements = []

        for policy in package_result.policies:
            # Get framework mappings from policy
            frameworks = policy.frameworks if hasattr(policy, 'frameworks') else {}

            for framework_id, controls in frameworks.items():
                if not isinstance(controls, list):
                    controls = [controls]

                for control_id in controls:
                    requirements.append({
                        "uuid": self._generate_uuid(f"impl-{policy.id}-{control_id}"),
                        "control-id": str(control_id),
                        "statements": [
                            {
                                "statement-id": f"{control_id}_smt",
                                "uuid": self._generate_uuid(f"stmt-{policy.id}-{control_id}"),
                                "description": f"Implemented through {policy.title}"
                            }
                        ],
                        "by-components": [
                            {
                                "component-uuid": self._generate_uuid(f"component-policies-{package_result.client_name}"),
                                "uuid": self._generate_uuid(f"by-comp-{policy.id}-{control_id}"),
                                "description": f"Control implemented by: {policy.title}",
                                "implementation-status": {
                                    "state": "implemented"
                                }
                            }
                        ]
                    })

        return requirements

    def export_component_definition(self, policies: List, output_path: str,
                                   component_name: str = "Policy Framework") -> str:
        """
        Export as OSCAL Component Definition.

        Component definitions describe security capabilities that can be
        applied to systems.

        Args:
            policies: List of policy objects
            output_path: Path to write JSON output
            component_name: Name for the component

        Returns:
            Path to the created file
        """
        component_def = {
            "component-definition": {
                "uuid": self._generate_uuid(f"compdef-{component_name}"),
                "metadata": {
                    "title": f"{component_name} Component Definition",
                    "last-modified": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "oscal-version": self.OSCAL_VERSION
                },
                "components": [
                    {
                        "uuid": self._generate_uuid(f"comp-{component_name}"),
                        "type": "policy",
                        "title": component_name,
                        "description": "Security policy framework providing organizational controls",
                        "control-implementations": self._build_control_implementations(policies)
                    }
                ]
            }
        }

        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(component_def, f, indent=2)

        logger.info(f"Exported OSCAL Component Definition to {output_path}")
        return str(output_path)

    def _build_control_implementations(self, policies) -> List[Dict]:
        """Build control implementations from policies"""
        implementations = []

        # Group by framework
        framework_controls = {}
        for policy in policies:
            frameworks = getattr(policy, 'frameworks', {})
            for fw_id, controls in frameworks.items():
                if fw_id not in framework_controls:
                    framework_controls[fw_id] = []

                if not isinstance(controls, list):
                    controls = [controls]

                for ctrl in controls:
                    framework_controls[fw_id].append({
                        'control': ctrl,
                        'policy': policy
                    })

        # Create implementation for each framework
        for fw_id, controls in framework_controls.items():
            impl = {
                "uuid": self._generate_uuid(f"ctrl-impl-{fw_id}"),
                "source": f"#{fw_id}",
                "description": f"Control implementation for {fw_id}",
                "implemented-requirements": []
            }

            for item in controls:
                impl["implemented-requirements"].append({
                    "uuid": self._generate_uuid(f"req-{fw_id}-{item['control']}"),
                    "control-id": str(item['control']),
                    "description": f"Implemented by: {item['policy'].title if hasattr(item['policy'], 'title') else item['policy'].get('title', 'Unknown')}"
                })

            implementations.append(impl)

        return implementations

    def export_catalog(self, framework_data: Dict, output_path: str) -> str:
        """
        Export a compliance framework as OSCAL Catalog.

        Args:
            framework_data: Framework definition dictionary
            output_path: Path to write JSON output

        Returns:
            Path to the created file
        """
        framework_id = framework_data.get('framework', {}).get('id', 'unknown')
        framework_name = framework_data.get('framework', {}).get('name', 'Unknown Framework')

        catalog = {
            "catalog": {
                "uuid": self._generate_uuid(f"catalog-{framework_id}"),
                "metadata": {
                    "title": framework_name,
                    "last-modified": datetime.now().isoformat(),
                    "version": framework_data.get('framework', {}).get('version', '1.0'),
                    "oscal-version": self.OSCAL_VERSION
                },
                "groups": self._build_catalog_groups(framework_data)
            }
        }

        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)

        logger.info(f"Exported OSCAL Catalog to {output_path}")
        return str(output_path)

    def _build_catalog_groups(self, framework_data) -> List[Dict]:
        """Build catalog groups from framework data"""
        groups = []
        framework = framework_data.get('framework', {})

        # Handle different framework structures
        if 'families' in framework:
            for family_id, family_data in framework['families'].items():
                group = {
                    "id": family_id,
                    "title": family_data.get('name', family_id),
                    "controls": []
                }

                for ctrl_id, ctrl_data in family_data.get('controls', {}).items():
                    group["controls"].append({
                        "id": ctrl_id,
                        "title": ctrl_data.get('name', ctrl_id),
                        "props": [
                            {"name": "label", "value": ctrl_id}
                        ]
                    })

                groups.append(group)

        elif 'controls' in framework:
            for ctrl_id, ctrl_data in framework['controls'].items():
                if isinstance(ctrl_data, dict) and 'safeguards' in ctrl_data:
                    # CIS-style with safeguards
                    group = {
                        "id": ctrl_id,
                        "title": ctrl_data.get('name', ctrl_id),
                        "controls": []
                    }

                    for sg_id, sg_data in ctrl_data['safeguards'].items():
                        group["controls"].append({
                            "id": sg_id,
                            "title": sg_data.get('name', sg_id)
                        })

                    groups.append(group)

        return groups


def export_package_to_oscal(package_result, output_dir: str, format: str = "ssp") -> List[str]:
    """
    Convenience function to export a package to OSCAL format.

    Args:
        package_result: PackageResult from generation
        output_dir: Directory for output files
        format: 'ssp', 'component', or 'all'

    Returns:
        List of created file paths
    """
    exporter = OscalExporter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []
    safe_name = package_result.client_name.lower().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d')

    if format in ['ssp', 'all']:
        ssp_path = output_dir / f"{safe_name}_ssp_{timestamp}.json"
        exporter.export_ssp(package_result, str(ssp_path))
        files.append(str(ssp_path))

    if format in ['component', 'all']:
        comp_path = output_dir / f"{safe_name}_component_{timestamp}.json"
        exporter.export_component_definition(
            package_result.policies,
            str(comp_path),
            component_name=f"{package_result.client_name} Policies"
        )
        files.append(str(comp_path))

    return files
