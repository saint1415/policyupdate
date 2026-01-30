#!/usr/bin/env python3
"""
Batch Policy Converter
Converts all DOCX policies to Markdown + YAML format
"""

import os
import sys
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent
sys.path.insert(0, str(project_dir / 'src'))

from core.policy_parser import PolicyParser, convert_docx_library

# Enhanced category mapping based on categories.yaml
POLICY_CATEGORY_MAP = {
    # Access Control
    'access-control-policy': 'access-control',
    'access-control-procedure': 'access-control',
    'account-management-policy': 'access-control',
    'admin-special-access-policy': 'access-control',
    'identification-and-authentication-policy': 'access-control',
    'logical-access-controls-policy': 'access-control',
    'password-policy': 'access-control',
    'physical-access-policy': 'access-control',
    'remote-access-policy': 'access-control',
    'user-privilege-policy': 'access-control',
    'vendor-access-policy': 'access-control',
    'guest-access-policy': 'access-control',

    # Network Security
    'network-security-policy': 'network-security',
    'network-configuration-policy': 'network-security',
    'network-documentation-policy': 'network-security',
    'network-address-policy': 'network-security',
    'firewall-policy': 'network-security',
    'firewall-procedure': 'network-security',
    'firewall-hardening-procedure': 'network-security',
    'router-security-policy': 'network-security',
    'wireless-access-policy': 'network-security',
    'vpn-policy': 'network-security',
    'domain-controller-policy': 'network-security',
    'domain-name-system-policy': 'network-security',
    'intrusion-dectection-policy': 'network-security',  # Note: typo in original
    'intrusion-detection-policy': 'network-security',

    # Data Protection
    'data-classification-policy': 'data-protection',
    'data-privacy-policy': 'data-protection',
    'data-retention-policy': 'data-protection',
    'data-integrity-policy': 'data-protection',
    'data-marking-policy': 'data-protection',
    'data-analytics-policy': 'data-protection',
    'encryption-policy': 'data-protection',
    'database-security-policy': 'data-protection',
    'disposal-policy': 'data-protection',

    # Business Continuity
    'business-continuity-policy': 'business-continuity',
    'business-continuity-plan': 'business-continuity',
    'business-continuity-business-resumption-plan': 'business-continuity',
    'business-continuity-communications-plan': 'business-continuity',
    'business-continuity-disaster-recovery-plan': 'business-continuity',
    'business-continuity-of-operations-department-plan': 'business-continuity',
    'business-impact-analysis': 'business-continuity',
    'incident-response-policy': 'business-continuity',
    'incident-response-plan': 'business-continuity',
    'backup-policy': 'business-continuity',
    'backup-procedure': 'business-continuity',
    'backup-plan': 'business-continuity',

    # Compliance
    'compliance-policy': 'compliance',
    'hipaa-and-hitech-policy': 'compliance',
    'hitrust-policy': 'compliance',
    'pci-policy': 'compliance',
    'gdpr-eu-privacy-and-data-protection-policy': 'compliance',
    'eu-privacy-and-data-protection-policy': 'compliance',
    'system-and-organization-controls-soc2-policy': 'compliance',
    'certification-and-accreditation-policy': 'compliance',

    # Operations
    'change-management-policy': 'operations',
    'change-management-procedure': 'operations',
    'configuration-management-policy': 'operations',
    'configuration-management-procedure': 'operations',
    'configuration-management-plan': 'operations',
    'patch-management-policy': 'operations',
    'patch-management-procedure': 'operations',
    'hardware-and-software-maintenance-policy': 'operations',
    'hardware-and-software-maintenance-procedure': 'operations',
    'problem-management-policy': 'operations',
    'problem-management-procedure': 'operations',
    'capacity-and-utilization-policy': 'operations',
    'system-update-policy': 'operations',

    # Endpoint Security
    'workstation-security-policy': 'endpoint-security',
    'workstation-hardening-policy': 'endpoint-security',
    'workstation-hardening-procedure': 'endpoint-security',
    'mobile-device-policy': 'endpoint-security',
    'smartphone-policy': 'endpoint-security',
    'portable-computing-policy': 'endpoint-security',
    'bring-your-own-device-and-technology-policy': 'endpoint-security',
    'removable-media-policy': 'endpoint-security',
    'bluetooth-policy': 'endpoint-security',
    'wearable-computing-device-policy': 'endpoint-security',

    # Vendor Management
    'third-party-service-providers-policy': 'vendor-management',
    'outsourcing-policy': 'vendor-management',
    'cloud-service-provider-policy': 'vendor-management',
    'acquistion-and-procurement-policy': 'vendor-management',  # Note: typo in original
    'mergers-and-acquisitions-policy': 'vendor-management',

    # Risk Management
    'risk-management-policy': 'risk-management',
    'risk-assessment-policy': 'risk-management',
    'vulnerability-and-penetration-testing-policy': 'risk-management',
    'security-self-assessment-policy': 'risk-management',
    'security-controls-review-policy': 'risk-management',

    # Personnel & Training
    'personnel-security-policy': 'personnel-training',
    'staffing-policy': 'personnel-training',
    'security-awareness-and-training-policy': 'personnel-training',
    'security-awareness-and-training-plan': 'personnel-training',
    'identity-theft-protection-policy': 'personnel-training',
    'reporting-violations-policy': 'personnel-training',

    # Development
    'software-development-policy': 'development',
    'secure-software-development-lifecycle-policy': 'development',
    'application-implementation-policy': 'development',
    'approved-application-policy': 'development',
    'software-licensing-policy': 'development',

    # Physical Security
    'physical-security-policy': 'physical-security',
    'facility-security-plan': 'physical-security',
    'clear-desk-policy': 'physical-security',

    # Audit & Monitoring
    'audit-policy': 'audit-monitoring',
    'audit-trails-policy': 'audit-monitoring',
    'logging-policy': 'audit-monitoring',
    'logging-procedure': 'audit-monitoring',
    'security-monitoring-policy': 'audit-monitoring',

    # Governance
    'it-governance-policy': 'governance',
    'it-management-policy': 'governance',
    'cybersecurity-policy': 'governance',
    'cybersecurity-framework-policy': 'governance',
    'information-security-policy': 'governance',
    'security-policy': 'governance',
    'context-and-alignment-policy': 'governance',

    # Communication & Web
    'e-mail-policy': 'communication',
    'internet-connection-policy': 'communication',
    'web-site-policy': 'communication',
    'web-site-privacy-policy': 'communication',
    'social-networking-policy': 'communication',
    'mass-communication-policy': 'communication',
    'e-commerce-policy': 'communication',

    # Anti-Malware
    'anti-malware-policy': 'malware-threats',
    'anti-malware-procedure': 'malware-threats',
    'ransomware-policy': 'malware-threats',

    # Documentation
    'documentation-policy': 'documentation',
    'standard-operating-procedure-policy': 'documentation',
    'terms-and-definitions-policy': 'documentation',
    'procedure-template': 'documentation',

    # Agreements
    'agreement-business-associate-agreement': 'agreements',
    'agreement-non-disclosure-agreement': 'agreements',
    'receipt-and-acknowledgement': 'agreements',

    # General
    'acceptable-use-policy': 'general',
    'ethics-policy': 'general',
    'privacy-policy': 'general',
    'green-computing-policy': 'general',
    'health-safety-policy': 'general',
    'resilience-policy': 'general',
    'production-input-output-controls-policy': 'general',
    'quality-assurance-policy': 'general',
    'securing-information-systems-policy': 'general',
    'securing-sensitive-information-policy': 'general',
    'server-certificates-policy': 'general',
    'server-hardening-policy': 'general',
    'server-hardening-procedure': 'general',
    'system-security-plan': 'general',
    'asset-management-policy': 'general',
}


class EnhancedPolicyParser(PolicyParser):
    """Enhanced parser with category mapping"""

    def _detect_category(self, title, doc=None):
        """Use explicit mapping first, then fall back to detection"""
        policy_id = self._generate_id(title)

        if policy_id in POLICY_CATEGORY_MAP:
            return POLICY_CATEGORY_MAP[policy_id]

        # Fall back to keyword detection
        return super()._detect_category(title, doc)


def main():
    # Paths
    source_dir = project_dir / 'current'
    output_dir = project_dir / 'policies'

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print()

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Get all DOCX files
    docx_files = sorted([f for f in os.listdir(source_dir)
                        if f.endswith('.docx') and not f.startswith('~')])

    print(f"Found {len(docx_files)} DOCX files to convert")
    print("=" * 60)

    # Convert each file
    parser = EnhancedPolicyParser()
    success = 0
    failed = 0
    results = {}

    for docx_file in docx_files:
        source_path = source_dir / docx_file

        try:
            policy = parser.parse_docx(str(source_path))
            output_path = parser.save_policy(policy, str(output_dir))
            results[docx_file] = {
                'status': 'success',
                'output': output_path,
                'category': policy.category,
                'id': policy.id
            }
            print(f"[OK] {docx_file}")
            print(f"     -> {output_path}")
            success += 1
        except Exception as e:
            results[docx_file] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"[ERROR] {docx_file}: {e}")
            failed += 1

    # Summary
    print()
    print("=" * 60)
    print(f"Conversion Complete: {success} succeeded, {failed} failed")
    print()

    # Category summary
    categories = {}
    for docx_file, result in results.items():
        if result['status'] == 'success':
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result['id'])

    print("Policies by Category:")
    for cat in sorted(categories.keys()):
        print(f"  {cat}: {len(categories[cat])} policies")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
