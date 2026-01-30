"""
Gap Analyzer Module
Identifies missing policies for compliance frameworks
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import yaml


@dataclass
class Gap:
    """A compliance gap"""
    framework_id: str
    control_id: str
    control_name: str
    control_description: str
    required_policies: List[str]
    missing_policies: List[str]
    available_policies: List[str]
    severity: str = "medium"
    category: str = ""

    @property
    def coverage_ratio(self) -> float:
        """Calculate coverage ratio for this control"""
        if not self.required_policies:
            return 1.0
        return len(self.available_policies) / len(self.required_policies)

    @property
    def is_fully_covered(self) -> bool:
        return len(self.missing_policies) == 0


@dataclass
class GapReport:
    """A comprehensive gap analysis report"""
    framework_id: str
    framework_name: str
    total_controls: int
    fully_covered_controls: int
    partially_covered_controls: int
    not_covered_controls: int
    total_required_policies: int
    available_policies: int
    missing_policies: int
    overall_coverage: float
    gaps: List[Gap]
    missing_policy_list: List[str]
    category_coverage: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization"""
        return {
            "framework_id": self.framework_id,
            "framework_name": self.framework_name,
            "summary": {
                "total_controls": self.total_controls,
                "fully_covered_controls": self.fully_covered_controls,
                "partially_covered_controls": self.partially_covered_controls,
                "not_covered_controls": self.not_covered_controls,
                "total_required_policies": self.total_required_policies,
                "available_policies": self.available_policies,
                "missing_policies": self.missing_policies,
                "overall_coverage_percentage": round(self.overall_coverage * 100, 1)
            },
            "missing_policy_list": self.missing_policy_list,
            "category_coverage": self.category_coverage,
            "gaps": [
                {
                    "control_id": g.control_id,
                    "control_name": g.control_name,
                    "category": g.category,
                    "severity": g.severity,
                    "required_policies": g.required_policies,
                    "missing_policies": g.missing_policies,
                    "coverage_ratio": g.coverage_ratio
                }
                for g in self.gaps if not g.is_fully_covered
            ]
        }


class GapAnalyzer:
    """Analyzes gaps between current policies and framework requirements"""

    def __init__(self, compliance_mapper=None, policy_library: Optional[Set[str]] = None):
        self.mapper = compliance_mapper
        self.library = policy_library or set()

    def set_policy_library(self, policy_ids: Set[str]) -> None:
        """Set the available policy library"""
        self.library = policy_ids

    def load_policy_library_from_dir(self, policies_dir: str) -> Set[str]:
        """Load policy IDs from a policies directory"""
        policies_path = Path(policies_dir)
        if not policies_path.exists():
            raise FileNotFoundError(f"Policies directory not found: {policies_dir}")

        policy_ids = set()
        for md_file in policies_path.rglob("*.md"):
            # Extract policy ID from frontmatter or filename
            policy_id = self._extract_policy_id(md_file)
            if policy_id:
                policy_ids.add(policy_id)

        self.library = policy_ids
        return policy_ids

    def _extract_policy_id(self, filepath: Path) -> Optional[str]:
        """Extract policy ID from file"""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Try to extract from YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter and 'id' in frontmatter:
                        return frontmatter['id']

            # Fall back to filename
            return filepath.stem

        except Exception:
            return filepath.stem

    def analyze_framework(self, framework_id: str) -> GapReport:
        """
        Analyze gaps for a specific framework

        Args:
            framework_id: Framework ID to analyze

        Returns:
            GapReport with detailed analysis
        """
        if not self.mapper:
            raise ValueError("No compliance mapper configured")

        framework = self.mapper.frameworks.get(framework_id)
        if not framework:
            raise ValueError(f"Framework not found: {framework_id}")

        gaps = []
        all_required = set()
        all_missing = set()
        category_stats = {}

        for control_id, control in framework.controls.items():
            required = set(control.policies_required)
            all_required.update(required)

            available = required & self.library
            missing = required - self.library

            # Track missing policies
            all_missing.update(missing)

            # Determine severity
            if len(missing) == len(required) and len(required) > 0:
                severity = "critical"
            elif len(missing) > len(available):
                severity = "high"
            elif len(missing) > 0:
                severity = "medium"
            else:
                severity = "none"

            gap = Gap(
                framework_id=framework_id,
                control_id=control_id,
                control_name=control.name,
                control_description=control.description,
                required_policies=list(required),
                missing_policies=list(missing),
                available_policies=list(available),
                severity=severity,
                category=control.parent_category or control.parent_function
            )
            gaps.append(gap)

            # Track category statistics
            category = control.parent_category or "Uncategorized"
            if category not in category_stats:
                category_stats[category] = {
                    "total_controls": 0,
                    "fully_covered": 0,
                    "partially_covered": 0,
                    "not_covered": 0,
                    "required_policies": set(),
                    "missing_policies": set()
                }

            category_stats[category]["total_controls"] += 1
            category_stats[category]["required_policies"].update(required)
            category_stats[category]["missing_policies"].update(missing)

            if gap.is_fully_covered:
                category_stats[category]["fully_covered"] += 1
            elif len(available) > 0:
                category_stats[category]["partially_covered"] += 1
            else:
                category_stats[category]["not_covered"] += 1

        # Calculate summary stats
        fully_covered = sum(1 for g in gaps if g.is_fully_covered)
        partially_covered = sum(1 for g in gaps if not g.is_fully_covered and len(g.available_policies) > 0)
        not_covered = sum(1 for g in gaps if len(g.available_policies) == 0 and len(g.required_policies) > 0)

        # Convert category stats sets to counts
        category_coverage = {}
        for cat, stats in category_stats.items():
            category_coverage[cat] = {
                "total_controls": stats["total_controls"],
                "fully_covered": stats["fully_covered"],
                "partially_covered": stats["partially_covered"],
                "not_covered": stats["not_covered"],
                "coverage_percentage": round(
                    (stats["fully_covered"] / stats["total_controls"]) * 100, 1
                ) if stats["total_controls"] > 0 else 0,
                "required_policies": len(stats["required_policies"]),
                "missing_policies": len(stats["missing_policies"])
            }

        # Sort gaps by severity, then by control ID (as string)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "none": 3}
        gaps.sort(key=lambda g: (severity_order.get(g.severity, 4), str(g.control_id)))

        return GapReport(
            framework_id=framework_id,
            framework_name=framework.name,
            total_controls=len(gaps),
            fully_covered_controls=fully_covered,
            partially_covered_controls=partially_covered,
            not_covered_controls=not_covered,
            total_required_policies=len(all_required),
            available_policies=len(all_required & self.library),
            missing_policies=len(all_missing),
            overall_coverage=fully_covered / len(gaps) if gaps else 0,
            gaps=gaps,
            missing_policy_list=sorted(all_missing),
            category_coverage=category_coverage
        )

    def analyze_multiple_frameworks(self, framework_ids: List[str]) -> Dict[str, GapReport]:
        """Analyze gaps for multiple frameworks"""
        reports = {}
        for fw_id in framework_ids:
            try:
                reports[fw_id] = self.analyze_framework(fw_id)
            except ValueError as e:
                print(f"Warning: {e}")
        return reports

    def get_priority_gaps(self, framework_id: str, limit: int = 10) -> List[Gap]:
        """Get highest priority gaps for a framework"""
        report = self.analyze_framework(framework_id)
        return [g for g in report.gaps if not g.is_fully_covered][:limit]

    def get_missing_policies_summary(self, framework_ids: List[str]) -> Dict[str, Any]:
        """Get summary of missing policies across frameworks"""
        all_missing = {}

        for fw_id in framework_ids:
            try:
                report = self.analyze_framework(fw_id)
                for policy_id in report.missing_policy_list:
                    if policy_id not in all_missing:
                        all_missing[policy_id] = {
                            "frameworks": [],
                            "controls": []
                        }
                    all_missing[policy_id]["frameworks"].append(fw_id)

                    # Find controls that need this policy
                    for gap in report.gaps:
                        if policy_id in gap.missing_policies:
                            all_missing[policy_id]["controls"].append(
                                f"{fw_id}:{gap.control_id}"
                            )
            except ValueError:
                continue

        # Sort by number of frameworks impacted
        sorted_missing = sorted(
            all_missing.items(),
            key=lambda x: (len(x[1]["frameworks"]), len(x[1]["controls"])),
            reverse=True
        )

        return {
            "total_missing": len(all_missing),
            "policies": [
                {
                    "policy_id": policy_id,
                    "frameworks_impacted": len(data["frameworks"]),
                    "controls_impacted": len(data["controls"]),
                    "framework_list": data["frameworks"]
                }
                for policy_id, data in sorted_missing
            ]
        }

    def generate_remediation_priorities(self,
                                         framework_ids: List[str],
                                         limit: int = 20) -> List[Dict[str, Any]]:
        """Generate prioritized list of policies to create"""
        missing_summary = self.get_missing_policies_summary(framework_ids)

        priorities = []
        for policy_data in missing_summary["policies"][:limit]:
            policy_id = policy_data["policy_id"]

            # Determine priority based on impact
            frameworks_impacted = policy_data["frameworks_impacted"]
            controls_impacted = policy_data["controls_impacted"]

            if frameworks_impacted >= 3 or controls_impacted >= 10:
                priority = "critical"
            elif frameworks_impacted >= 2 or controls_impacted >= 5:
                priority = "high"
            else:
                priority = "medium"

            priorities.append({
                "policy_id": policy_id,
                "priority": priority,
                "frameworks_impacted": frameworks_impacted,
                "controls_impacted": controls_impacted,
                "framework_list": policy_data["framework_list"],
                "recommendation": f"Create {policy_id} to address {controls_impacted} controls across {frameworks_impacted} framework(s)"
            })

        return priorities


def main():
    """Test the gap analyzer"""
    import sys
    from pathlib import Path

    # Import compliance mapper
    from compliance_mapper import ComplianceMapper

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    frameworks_dir = project_root / "config" / "frameworks"
    policies_dir = project_root / "policies"

    print("=" * 70)
    print("GAP ANALYZER TEST")
    print("=" * 70)

    # Load compliance mapper
    print("\nLoading compliance frameworks...")
    mapper = ComplianceMapper()
    mapper.load_all_frameworks(str(frameworks_dir))
    print(f"Loaded {len(mapper.frameworks)} frameworks")

    # Initialize gap analyzer
    analyzer = GapAnalyzer(compliance_mapper=mapper)

    # Load policy library
    print(f"\nLoading policy library from: {policies_dir}")
    if policies_dir.exists():
        policy_ids = analyzer.load_policy_library_from_dir(str(policies_dir))
        print(f"Loaded {len(policy_ids)} policies")
    else:
        print("Policies directory not found, using empty library")

    # Analyze each framework
    print("\n" + "=" * 70)
    print("GAP ANALYSIS BY FRAMEWORK")
    print("=" * 70)

    for fw_id in mapper.frameworks.keys():
        report = analyzer.analyze_framework(fw_id)
        print(f"\n{report.framework_name}")
        print("-" * 50)
        print(f"  Total Controls: {report.total_controls}")
        print(f"  Fully Covered: {report.fully_covered_controls} ({round(report.overall_coverage * 100, 1)}%)")
        print(f"  Partially Covered: {report.partially_covered_controls}")
        print(f"  Not Covered: {report.not_covered_controls}")
        print(f"  Required Policies: {report.total_required_policies}")
        print(f"  Available: {report.available_policies}")
        print(f"  Missing: {report.missing_policies}")

        if report.missing_policy_list[:5]:
            print(f"  Top Missing: {', '.join(report.missing_policy_list[:5])}")

    # Cross-framework priority analysis
    print("\n" + "=" * 70)
    print("REMEDIATION PRIORITIES (Cross-Framework)")
    print("=" * 70)

    priorities = analyzer.generate_remediation_priorities(
        list(mapper.frameworks.keys()),
        limit=15
    )

    for i, item in enumerate(priorities, 1):
        print(f"\n{i}. [{item['priority'].upper()}] {item['policy_id']}")
        print(f"   Impacts: {item['frameworks_impacted']} frameworks, {item['controls_impacted']} controls")
        print(f"   Frameworks: {', '.join(item['framework_list'])}")


if __name__ == "__main__":
    main()
