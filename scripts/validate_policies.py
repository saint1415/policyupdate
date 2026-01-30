#!/usr/bin/env python3
"""
Policy Validation Script
Validates converted Markdown + YAML policies
"""

import os
import sys
import yaml
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent
sys.path.insert(0, str(project_dir / 'src'))


def validate_frontmatter(content: str) -> tuple:
    """Validate YAML frontmatter"""
    if not content.startswith('---'):
        return False, "Missing YAML frontmatter delimiter"

    try:
        # Find end of frontmatter
        end_idx = content.find('---', 3)
        if end_idx == -1:
            return False, "Missing closing YAML frontmatter delimiter"

        yaml_content = content[3:end_idx].strip()
        metadata = yaml.safe_load(yaml_content)

        # Check required fields
        required = ['id', 'title', 'category', 'type', 'status']
        missing = [f for f in required if f not in metadata]
        if missing:
            return False, f"Missing required fields: {missing}"

        return True, metadata

    except yaml.YAMLError as e:
        return False, f"YAML parse error: {e}"


def validate_content(content: str) -> dict:
    """Validate policy content structure"""
    issues = []

    # Check for markdown content after frontmatter
    end_idx = content.find('---', 3)
    if end_idx != -1:
        body = content[end_idx + 3:].strip()
        if not body:
            issues.append("Empty policy body")
        else:
            # Check for section headings
            if '##' not in body and '# ' not in body:
                issues.append("No section headings found")

            # Check approximate length
            if len(body) < 200:
                issues.append(f"Policy body very short ({len(body)} chars)")

    return issues


def main():
    policies_dir = project_dir / 'policies'

    print("=" * 70)
    print("POLICY VALIDATION REPORT")
    print("=" * 70)

    total = 0
    valid = 0
    warnings = 0
    errors = 0

    category_stats = {}
    all_ids = []
    all_references = []

    for category_dir in sorted(policies_dir.iterdir()):
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name
        category_stats[category_name] = {'total': 0, 'valid': 0, 'errors': []}

        for policy_file in sorted(category_dir.glob('*.md')):
            total += 1
            category_stats[category_name]['total'] += 1

            with open(policy_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate frontmatter
            fm_valid, fm_result = validate_frontmatter(content)

            if not fm_valid:
                errors += 1
                category_stats[category_name]['errors'].append(
                    f"{policy_file.name}: {fm_result}"
                )
                continue

            metadata = fm_result
            all_ids.append(metadata['id'])

            # Track references
            if metadata.get('references'):
                all_references.extend(metadata['references'])

            # Validate content
            content_issues = validate_content(content)
            if content_issues:
                warnings += 1
                for issue in content_issues:
                    category_stats[category_name]['errors'].append(
                        f"{policy_file.name}: WARNING - {issue}"
                    )
            else:
                valid += 1
                category_stats[category_name]['valid'] += 1

    # Summary
    print()
    print("SUMMARY")
    print("-" * 70)
    print(f"Total policies:     {total}")
    print(f"Valid policies:     {valid}")
    print(f"With warnings:      {warnings}")
    print(f"With errors:        {errors}")
    print()

    # Category breakdown
    print("BY CATEGORY")
    print("-" * 70)
    for cat, stats in sorted(category_stats.items()):
        status = "[OK]" if stats['total'] == stats['valid'] else "[!!]"
        print(f"  {status} {cat}: {stats['valid']}/{stats['total']}")

    # Show errors
    print()
    print("ISSUES")
    print("-" * 70)
    issue_count = 0
    for cat, stats in sorted(category_stats.items()):
        if stats['errors']:
            for err in stats['errors']:
                print(f"  [{cat}] {err}")
                issue_count += 1
                if issue_count >= 20:  # Limit output
                    print(f"  ... and more (showing first 20)")
                    break
        if issue_count >= 20:
            break

    # Reference validation
    print()
    print("REFERENCE VALIDATION")
    print("-" * 70)
    unique_refs = set(all_references)
    valid_refs = set(all_ids)
    broken_refs = unique_refs - valid_refs

    print(f"  Total unique references: {len(unique_refs)}")
    print(f"  Valid references:        {len(unique_refs - broken_refs)}")
    print(f"  Broken references:       {len(broken_refs)}")

    if broken_refs:
        print()
        print("  Broken reference targets (may need new policies):")
        for ref in sorted(broken_refs)[:20]:
            print(f"    - {ref}")

    # Field stats
    print()
    print("METADATA COVERAGE")
    print("-" * 70)

    # Check what variables were detected
    all_vars = set()
    for category_dir in policies_dir.iterdir():
        if not category_dir.is_dir():
            continue
        for policy_file in category_dir.glob('*.md'):
            with open(policy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            fm_valid, fm_result = validate_frontmatter(content)
            if fm_valid and fm_result.get('variables'):
                all_vars.update(fm_result['variables'])

    print(f"  Variables detected: {sorted(all_vars)}")

    print()
    print("=" * 70)
    print(f"VALIDATION {'PASSED' if errors == 0 else 'FAILED'}")
    print("=" * 70)

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
