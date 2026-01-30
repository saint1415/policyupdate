#!/usr/bin/env python3
"""
Add Framework Mappings to Policy Frontmatter

This script updates all policy files to include their compliance
framework mappings in the YAML frontmatter.
"""

import sys
import yaml
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

from core.compliance_mapper import ComplianceMapper


def load_policy(filepath: Path) -> tuple:
    """Load a policy file and return (frontmatter_dict, content, raw_text)"""
    content = filepath.read_text(encoding='utf-8')

    if not content.startswith('---'):
        return None, content, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
        return frontmatter, body, content
    except yaml.YAMLError:
        return None, content, content


def save_policy(filepath: Path, frontmatter: dict, body: str) -> None:
    """Save policy with updated frontmatter"""
    # Custom YAML dumper to preserve formatting
    yaml_content = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120
    )

    content = f"---\n{yaml_content}---{body}"
    filepath.write_text(content, encoding='utf-8')


def get_framework_controls(policy_id: str, mapper: ComplianceMapper) -> dict:
    """Get framework controls for a policy"""
    mapping = mapper.get_policy_frameworks(policy_id)

    # Clean up control IDs (remove * suffix for recommended)
    frameworks = {}
    for fw_id, controls in mapping.items():
        # Only include required controls (without * suffix)
        # Convert to string first to handle any numeric-like IDs
        required_controls = [str(c) for c in controls if not str(c).endswith('*')]
        if required_controls:
            frameworks[fw_id] = sorted(required_controls)

    return frameworks


def main():
    # Load compliance mapper
    frameworks_dir = project_root / "config" / "frameworks"
    policies_dir = project_root / "policies"

    print("Loading compliance frameworks...")
    mapper = ComplianceMapper()
    mapper.load_all_frameworks(str(frameworks_dir))
    print(f"Loaded {len(mapper.frameworks)} frameworks")

    # Process all policy files
    print(f"\nProcessing policies in: {policies_dir}")
    print("=" * 60)

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for md_file in sorted(policies_dir.rglob("*.md")):
        frontmatter, body, raw = load_policy(md_file)

        if frontmatter is None:
            print(f"SKIP (no frontmatter): {md_file.name}")
            skipped_count += 1
            continue

        policy_id = frontmatter.get('id', md_file.stem)

        # Get framework mappings
        frameworks = get_framework_controls(policy_id, mapper)

        if not frameworks:
            # No mappings found
            skipped_count += 1
            continue

        # Check if already has frameworks
        existing = frontmatter.get('frameworks', {})

        # Update frontmatter
        frontmatter['frameworks'] = frameworks

        try:
            save_policy(md_file, frontmatter, body)
            updated_count += 1

            total_controls = sum(len(c) for c in frameworks.values())
            print(f"UPDATED: {policy_id} -> {len(frameworks)} frameworks, {total_controls} controls")

        except Exception as e:
            print(f"ERROR: {md_file.name}: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")


if __name__ == "__main__":
    main()
