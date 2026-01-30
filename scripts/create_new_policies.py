#!/usr/bin/env python3
"""
Create New Policy Templates
Generates policy templates for new categories
"""

import os
from pathlib import Path
from datetime import datetime

# New policies to create with their content
NEW_POLICIES = {
    # AI Governance
    'ai-governance': {
        'ai-ml-governance-policy': {
            'title': 'AI/ML Governance Policy',
            'description': '''This policy establishes the governance framework for artificial intelligence and machine learning systems within {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} recognizes the transformative potential of AI/ML technologies while acknowledging the risks they present. This policy ensures AI/ML systems are developed, deployed, and managed responsibly.

## II. Purpose

To establish guidelines for the ethical development, deployment, monitoring, and governance of AI and machine learning systems.

## III. Scope

This policy applies to all AI/ML systems developed, procured, or deployed by {{ORGANIZATION_NAME}}, including:
- Machine learning models
- Natural language processing systems
- Computer vision systems
- Automated decision-making systems
- Generative AI tools

## IV. Policy

### A. AI Development Standards

1. All AI/ML projects must undergo risk assessment before development
2. Model training data must be documented and validated for bias
3. Model performance metrics must be established and monitored
4. Human oversight must be maintained for high-risk decisions

### B. Ethical AI Principles

1. **Fairness**: AI systems must not discriminate based on protected characteristics
2. **Transparency**: AI decision-making processes must be explainable
3. **Accountability**: Clear ownership and responsibility for AI systems
4. **Privacy**: AI systems must comply with data protection requirements

### C. Risk Categories

| Category | Description | Oversight Level |
|----------|-------------|-----------------|
| Low Risk | Internal tools, non-critical | Standard review |
| Medium Risk | Customer-facing, operational | Enhanced review |
| High Risk | Autonomous decisions, regulated | Executive approval |

### D. Monitoring and Auditing

1. Regular model performance reviews
2. Bias and fairness audits
3. Incident tracking and reporting
4. Model versioning and change management

## V. Compliance

This policy supports compliance with:
- EU AI Act
- NIST AI Risk Management Framework
- ISO/IEC 42001 (AI Management System)

## VI. Enforcement

Violations may result in project suspension, disciplinary action, or regulatory reporting.

## VII. Distribution

This policy shall be distributed to all personnel involved in AI/ML development, procurement, or deployment.
''',
        },
        'ai-ethics-policy': {
            'title': 'AI Ethics Policy',
            'description': '''This policy establishes ethical principles and guidelines for artificial intelligence at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} is committed to the ethical development and use of AI technologies that respect human rights, promote fairness, and maintain public trust.

## II. Purpose

To define ethical principles, guidelines, and governance structures for AI development and deployment.

## III. Scope

All AI initiatives, projects, and deployments within {{ORGANIZATION_NAME}}.

## IV. Ethical Principles

### A. Human-Centered Design

1. AI systems shall augment human capabilities, not replace human judgment inappropriately
2. Human oversight shall be maintained for consequential decisions
3. Users shall be informed when interacting with AI systems

### B. Fairness and Non-Discrimination

1. AI systems shall be tested for bias before deployment
2. Protected characteristics shall not be used inappropriately
3. Disparate impact shall be monitored and mitigated

### C. Transparency and Explainability

1. AI decision processes shall be documented
2. Explanations shall be provided for AI-driven decisions affecting individuals
3. Model limitations shall be communicated to users

### D. Privacy and Data Protection

1. Data minimization principles shall apply to AI training
2. Personal data used in AI shall comply with privacy policies
3. Data subjects' rights shall be respected

### E. Safety and Security

1. AI systems shall undergo security testing
2. Adversarial attack vectors shall be assessed
3. Fail-safe mechanisms shall be implemented

## V. Governance

1. AI Ethics Committee shall review high-risk AI deployments
2. Ethics review is required for novel AI applications
3. Regular ethics training for AI practitioners

## VI. Enforcement

Ethical violations shall be reported and investigated. Consequences may include project suspension.
''',
        },
        'algorithmic-accountability-policy': {
            'title': 'Algorithmic Accountability Policy',
            'description': '''This policy establishes accountability requirements for algorithmic and automated decision-making systems.

## I. Overview

{{ORGANIZATION_NAME}} maintains accountability for algorithmic systems that impact customers, employees, or business operations.

## II. Purpose

To ensure algorithmic systems are auditable, explainable, and subject to appropriate oversight.

## III. Scope

All automated decision-making systems including:
- Credit and risk scoring
- Fraud detection
- Content moderation
- Hiring and HR automation
- Customer service automation

## IV. Policy

### A. Documentation Requirements

1. Algorithm purpose and intended use
2. Input data sources and features
3. Decision logic and thresholds
4. Performance metrics and benchmarks
5. Known limitations and failure modes

### B. Impact Assessment

1. Pre-deployment impact assessment required
2. Affected populations must be identified
3. Potential harms must be evaluated
4. Mitigation measures must be documented

### C. Audit Trail

1. Decisions must be logged with timestamps
2. Input data must be retained for audit
3. Model versions must be tracked
4. Appeals processes must be documented

### D. Human Review

1. High-impact decisions require human review option
2. Appeals mechanism must be available
3. Override procedures must be documented

## V. Compliance

Supports compliance with:
- NYC Local Law 144 (AI in hiring)
- CCPA automated decision-making rights
- GDPR Article 22

## VI. Enforcement

Non-compliance may result in system suspension and regulatory reporting.
''',
        },
    },

    # Supply Chain Security
    'supply-chain': {
        'supply-chain-security-policy': {
            'title': 'Supply Chain Security Policy',
            'description': '''This policy establishes requirements for securing the supply chain at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} recognizes that supply chain risks can significantly impact security posture. This policy addresses supply chain risk management.

## II. Purpose

To establish controls for identifying, assessing, and mitigating supply chain security risks.

## III. Scope

All suppliers, vendors, contractors, and third-party providers of:
- Software and hardware
- Cloud services
- Professional services
- Manufacturing components

## IV. Policy

### A. Supplier Assessment

1. Security questionnaires for all critical suppliers
2. Risk-based tiering of suppliers
3. Due diligence before onboarding
4. Regular reassessment schedule

### B. Contractual Requirements

1. Security requirements in contracts
2. Right to audit clauses
3. Incident notification requirements
4. Data handling obligations

### C. Software Supply Chain

1. Source code review for critical components
2. Dependency scanning and monitoring
3. Software bill of materials (SBOM) requirements
4. Secure development attestations

### D. Monitoring and Response

1. Continuous monitoring of supplier security
2. Threat intelligence integration
3. Incident response coordination
4. Supply chain attack playbooks

## V. Risk Categories

| Tier | Criteria | Requirements |
|------|----------|--------------|
| Critical | Business essential, data access | Full assessment, annual audit |
| High | Significant access or impact | Security questionnaire, review |
| Medium | Limited access | Basic assessment |
| Low | Minimal risk | Standard terms |

## VI. Compliance

Supports NIST 800-161, ISO 28000, and C-SCRM requirements.
''',
        },
        'sbom-management-policy': {
            'title': 'SBOM Management Policy',
            'description': '''This policy establishes requirements for Software Bill of Materials (SBOM) management.

## I. Overview

{{ORGANIZATION_NAME}} requires visibility into software components to manage security vulnerabilities and licensing compliance.

## II. Purpose

To establish requirements for generating, maintaining, and utilizing SBOMs across the software portfolio.

## III. Scope

All software developed, procured, or deployed by {{ORGANIZATION_NAME}}.

## IV. Policy

### A. SBOM Generation

1. All internally developed software shall have SBOMs
2. SBOMs shall be generated during CI/CD pipeline
3. Standard formats (SPDX, CycloneDX) shall be used
4. SBOMs shall be version-controlled

### B. SBOM Content

Required elements:
- Component name and version
- Supplier information
- Unique identifiers (CPE, PURL)
- Dependency relationships
- License information
- Hash values for integrity

### C. Vendor Requirements

1. Request SBOMs from software vendors
2. Include SBOM requirements in procurement
3. Evaluate vendor SBOM maturity
4. Track vendor SBOM delivery

### D. Vulnerability Management

1. Correlate SBOMs with vulnerability databases
2. Prioritize remediation based on exposure
3. Track component end-of-life dates
4. Maintain component inventory

## V. Compliance

Supports Executive Order 14028, NTIA SBOM requirements.
''',
        },
        'software-supply-chain-policy': {
            'title': 'Software Supply Chain Policy',
            'description': '''This policy establishes security requirements for the software supply chain.

## I. Overview

{{ORGANIZATION_NAME}} implements controls to protect against software supply chain attacks and compromises.

## II. Purpose

To secure the software development and distribution pipeline from threats.

## III. Scope

All software development, build, and distribution processes.

## IV. Policy

### A. Secure Development

1. Secure coding standards enforcement
2. Code review requirements
3. Static and dynamic analysis
4. Dependency vulnerability scanning

### B. Build Security

1. Hardened build environments
2. Build reproducibility
3. Artifact signing
4. Build provenance attestation

### C. Distribution Security

1. Secure artifact repositories
2. Package signing and verification
3. Distribution channel integrity
4. Update mechanism security

### D. Third-Party Code

1. Open source component vetting
2. License compliance verification
3. Maintainer assessment
4. Forking strategy for critical dependencies

## V. Compliance

Supports SLSA framework, SSDF requirements.
''',
        },
    },

    # Zero Trust
    'zero-trust': {
        'zero-trust-architecture-policy': {
            'title': 'Zero Trust Architecture Policy',
            'description': '''This policy establishes the Zero Trust security architecture for {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} adopts Zero Trust principles: never trust, always verify. This policy defines the strategic approach to Zero Trust implementation.

## II. Purpose

To establish a security architecture based on Zero Trust principles that eliminates implicit trust.

## III. Scope

All network access, applications, data, and users within {{ORGANIZATION_NAME}}.

## IV. Core Principles

### A. Verify Explicitly

1. Authenticate and authorize every access request
2. Use multiple factors for verification
3. Consider user, device, location, and behavior
4. Continuous validation throughout session

### B. Least Privilege Access

1. Just-in-time access provisioning
2. Just-enough-access permissions
3. Risk-based adaptive policies
4. Regular access reviews

### C. Assume Breach

1. Segment networks and resources
2. Encrypt data in transit and at rest
3. Monitor all activity
4. Prepare incident response

## V. Architecture Components

### A. Identity

1. Strong identity verification
2. Multi-factor authentication
3. Single sign-on integration
4. Identity governance

### B. Devices

1. Device health validation
2. Endpoint detection and response
3. Mobile device management
4. Device compliance policies

### C. Network

1. Micro-segmentation
2. Software-defined perimeter
3. Encrypted communications
4. Network access control

### D. Data

1. Data classification
2. Data loss prevention
3. Encryption at rest
4. Access logging

## VI. Compliance

Supports NIST 800-207, CISA Zero Trust Maturity Model.
''',
        },
        'zero-trust-implementation-procedure': {
            'title': 'Zero Trust Implementation Procedure',
            'description': '''This procedure provides implementation guidance for Zero Trust architecture.

## I. Overview

Step-by-step guidance for implementing Zero Trust at {{ORGANIZATION_NAME}}.

## II. Implementation Phases

### Phase 1: Assessment (Months 1-2)

1. Inventory all assets and data flows
2. Identify protect surfaces
3. Map transaction flows
4. Assess current security controls
5. Define Zero Trust scope

### Phase 2: Identity Foundation (Months 3-4)

1. Deploy identity provider
2. Implement MFA everywhere
3. Establish device trust
4. Configure conditional access
5. Enable SSO integration

### Phase 3: Network Segmentation (Months 5-6)

1. Implement micro-segmentation
2. Deploy software-defined perimeter
3. Configure access policies
4. Enable network monitoring
5. Test access controls

### Phase 4: Application Security (Months 7-8)

1. Implement application access proxy
2. Deploy API gateway
3. Enable application-level encryption
4. Configure application policies
5. Integrate with identity

### Phase 5: Data Protection (Months 9-10)

1. Classify sensitive data
2. Deploy DLP controls
3. Enable data encryption
4. Configure data access policies
5. Monitor data flows

### Phase 6: Continuous Improvement (Ongoing)

1. Monitor and analyze
2. Adjust policies based on risk
3. Expand Zero Trust scope
4. Address new use cases
5. Regular architecture reviews

## III. Success Metrics

- Reduction in lateral movement incidents
- MFA adoption rate
- Network segmentation coverage
- Policy violation trends
''',
        },
    },

    # Cryptography
    'cryptography': {
        'quantum-safe-cryptography-policy': {
            'title': 'Quantum-Safe Cryptography Policy',
            'description': '''This policy establishes requirements for quantum-resistant cryptography at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} prepares for the quantum computing era by adopting quantum-safe cryptographic standards.

## II. Purpose

To protect long-term sensitive data against future quantum computing threats.

## III. Scope

All cryptographic systems protecting data with long-term confidentiality requirements.

## IV. Policy

### A. Cryptographic Inventory

1. Identify all cryptographic implementations
2. Document algorithms and key sizes
3. Assess quantum vulnerability
4. Prioritize migration targets

### B. Algorithm Standards

**Current Requirements:**
- RSA: Minimum 3072-bit keys
- ECC: Minimum 256-bit curves
- AES: 256-bit for long-term data

**Quantum-Safe Migration:**
- NIST PQC algorithms when finalized
- Hybrid classical/PQC during transition
- Crypto-agility in new systems

### C. Data Classification

| Classification | Sensitivity Duration | Action |
|---------------|---------------------|--------|
| Top Secret | 50+ years | Immediate PQC planning |
| Secret | 25+ years | PQC migration priority |
| Confidential | 10+ years | Monitor PQC readiness |
| Internal | <10 years | Standard updates |

### D. Implementation Requirements

1. Crypto-agility in all new systems
2. Algorithm abstraction layers
3. Key size upgrade paths
4. Regular algorithm reviews

## V. Compliance

Supports NIST PQC standards, NSA CNSA 2.0.
''',
        },
        'key-management-policy': {
            'title': 'Key Management Policy',
            'description': '''This policy establishes requirements for cryptographic key management.

## I. Overview

{{ORGANIZATION_NAME}} implements secure key management practices to protect cryptographic assets.

## II. Purpose

To ensure cryptographic keys are generated, distributed, stored, rotated, and destroyed securely.

## III. Scope

All cryptographic keys used within {{ORGANIZATION_NAME}}.

## IV. Policy

### A. Key Generation

1. Keys generated using approved random number generators
2. Key generation in secure environments
3. Key strength appropriate for use case
4. Generation process documented and auditable

### B. Key Distribution

1. Secure key exchange protocols
2. Out-of-band verification for manual distribution
3. Key wrapping for storage and transit
4. Distribution audit trails

### C. Key Storage

1. Hardware security modules for sensitive keys
2. Encryption of stored keys
3. Access controls on key stores
4. Backup and recovery procedures

### D. Key Rotation

| Key Type | Rotation Frequency |
|----------|-------------------|
| Root CA | 10-20 years |
| Intermediate CA | 5-10 years |
| TLS certificates | 1 year |
| API keys | 90 days |
| Encryption keys | Per data classification |

### E. Key Revocation and Destruction

1. Immediate revocation capability
2. Secure key destruction methods
3. Certificate revocation lists
4. Destruction verification

## V. Compliance

Supports PCI DSS 4.0, NIST 800-57.
''',
        },
        'certificate-lifecycle-policy': {
            'title': 'Certificate Lifecycle Policy',
            'description': '''This policy establishes requirements for digital certificate management.

## I. Overview

{{ORGANIZATION_NAME}} manages digital certificates throughout their lifecycle to ensure security and availability.

## II. Purpose

To establish standards for certificate issuance, renewal, and revocation.

## III. Scope

All digital certificates including TLS/SSL, code signing, and authentication certificates.

## IV. Policy

### A. Certificate Authority

1. Internal PKI for internal certificates
2. Trusted public CAs for external certificates
3. CA security requirements
4. Root trust management

### B. Certificate Issuance

1. Validated certificate requests
2. Appropriate key sizes and algorithms
3. Proper subject names and SANs
4. Certificate policy compliance

### C. Certificate Monitoring

1. Certificate inventory maintained
2. Expiration monitoring and alerting
3. Certificate transparency monitoring
4. Revocation status monitoring

### D. Certificate Renewal

1. Automated renewal where possible
2. 30-day renewal window minimum
3. Testing before production deployment
4. Rollback procedures

### E. Certificate Revocation

1. Immediate revocation for compromise
2. CRL and OCSP configuration
3. Revocation verification
4. Incident documentation

## V. Automation

1. ACME protocol for automated issuance
2. Certificate management platform
3. Integration with secret management
4. Automated compliance scanning

## VI. Compliance

Supports CA/Browser Forum requirements, PCI DSS.
''',
        },
    },

    # API Security
    'api-security': {
        'api-security-policy': {
            'title': 'API Security Policy',
            'description': '''This policy establishes security requirements for APIs at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} secures APIs as critical business assets requiring protection.

## II. Purpose

To establish standards for secure API development, deployment, and management.

## III. Scope

All APIs developed or consumed by {{ORGANIZATION_NAME}}, including REST, GraphQL, and gRPC.

## IV. Policy

### A. Authentication

1. OAuth 2.0 / OpenID Connect for user-facing APIs
2. API keys with rotation for service-to-service
3. Mutual TLS for sensitive integrations
4. No basic authentication for production

### B. Authorization

1. Principle of least privilege
2. Scope-based access control
3. Rate limiting per client
4. Resource-level permissions

### C. Input Validation

1. Schema validation for all inputs
2. Parameter type checking
3. Size limits enforcement
4. Injection prevention

### D. Transport Security

1. TLS 1.2+ required
2. Certificate pinning for mobile apps
3. HSTS headers
4. No sensitive data in URLs

### E. API Management

1. API gateway deployment
2. API versioning strategy
3. Deprecation policy
4. API documentation requirements

### F. Monitoring

1. Request/response logging
2. Anomaly detection
3. Abuse detection
4. Security event alerting

## V. OWASP API Security Top 10

Address all OWASP API Security risks including:
- Broken Object Level Authorization
- Broken Authentication
- Excessive Data Exposure
- Resource Consumption

## VI. Compliance

Supports PCI DSS API requirements, NIST guidelines.
''',
        },
        'integration-security-policy': {
            'title': 'Integration Security Policy',
            'description': '''This policy establishes security requirements for system integrations.

## I. Overview

{{ORGANIZATION_NAME}} secures integrations between internal and external systems.

## II. Purpose

To ensure integrations maintain security while enabling business connectivity.

## III. Scope

All system integrations including APIs, file transfers, databases, and messaging.

## IV. Policy

### A. Integration Patterns

1. API-first integration preferred
2. Message queue for async processing
3. Secure file transfer for batch
4. Direct database access prohibited

### B. Authentication

1. Service accounts with limited scope
2. Credential rotation requirements
3. No shared credentials
4. Secrets management integration

### C. Data Security

1. Encryption in transit required
2. Data minimization in transfers
3. Sensitive data masking
4. Audit logging

### D. Error Handling

1. No sensitive data in errors
2. Graceful failure handling
3. Circuit breaker patterns
4. Retry with backoff

### E. Third-Party Integrations

1. Security assessment required
2. Contractual security requirements
3. Data handling agreements
4. Regular security reviews

## V. Compliance

Supports SOC 2, data protection requirements.
''',
        },
    },

    # DevSecOps
    'devsecops': {
        'devsecops-policy': {
            'title': 'DevSecOps Policy',
            'description': '''This policy establishes DevSecOps practices at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} integrates security throughout the software development lifecycle.

## II. Purpose

To embed security into development processes, enabling secure and rapid delivery.

## III. Scope

All software development activities at {{ORGANIZATION_NAME}}.

## IV. Policy

### A. Shift Left Security

1. Security requirements in user stories
2. Threat modeling in design
3. Secure coding training
4. Security champions program

### B. Automated Security Testing

1. SAST in pull requests
2. DAST in staging environments
3. SCA for dependencies
4. Container scanning

### C. Security Gates

| Stage | Security Checks |
|-------|----------------|
| Commit | Secrets scanning, linting |
| Build | SAST, dependency scan |
| Deploy | DAST, compliance scan |
| Runtime | WAF, monitoring |

### D. Vulnerability Management

1. Severity-based SLAs
2. Automated ticket creation
3. Developer remediation
4. Exception process

### E. Infrastructure as Code

1. IaC security scanning
2. Policy as code
3. Configuration compliance
4. Drift detection

## V. Metrics

- Mean time to remediate
- Vulnerability escape rate
- Security test coverage
- Security debt trends

## VI. Compliance

Supports SSDF, NIST 800-218.
''',
        },
        'cicd-security-policy': {
            'title': 'CI/CD Security Policy',
            'description': '''This policy establishes security requirements for CI/CD pipelines.

## I. Overview

{{ORGANIZATION_NAME}} secures continuous integration and delivery pipelines.

## II. Purpose

To protect the software delivery pipeline from compromise.

## III. Scope

All CI/CD systems, build servers, and deployment automation.

## IV. Policy

### A. Pipeline Security

1. Pipeline as code in version control
2. Approval gates for production
3. Environment separation
4. Audit logging

### B. Build Security

1. Hardened build agents
2. Ephemeral build environments
3. No secrets in code
4. Artifact signing

### C. Access Control

1. Role-based pipeline access
2. Approval requirements
3. Service account governance
4. MFA for pipeline administration

### D. Secrets Management

1. Centralized secrets management
2. Just-in-time secret injection
3. No secrets in logs
4. Secret rotation

### E. Artifact Security

1. Artifact integrity verification
2. Vulnerability scanning
3. License compliance
4. Retention policies

## V. Compliance

Supports SLSA, SOC 2.
''',
        },
        'infrastructure-as-code-policy': {
            'title': 'Infrastructure as Code Policy',
            'description': '''This policy establishes requirements for Infrastructure as Code (IaC).

## I. Overview

{{ORGANIZATION_NAME}} manages infrastructure through code for consistency and security.

## II. Purpose

To ensure infrastructure is defined, versioned, and secured as code.

## III. Scope

All infrastructure provisioning and configuration management.

## IV. Policy

### A. IaC Standards

1. Approved IaC tools (Terraform, CloudFormation, etc.)
2. Module standardization
3. Naming conventions
4. Tagging requirements

### B. Version Control

1. All IaC in version control
2. Branch protection rules
3. Code review requirements
4. Change documentation

### C. Security Scanning

1. Pre-commit security checks
2. Policy compliance scanning
3. Secret detection
4. Drift detection

### D. State Management

1. Secure state storage
2. State locking
3. State encryption
4. Access controls

### E. Deployment

1. Plan review before apply
2. Approval workflows
3. Rollback procedures
4. Change tracking

## V. Compliance

Supports CIS benchmarks, cloud security best practices.
''',
        },
    },

    # Secrets Management
    'secrets-management': {
        'secrets-management-policy': {
            'title': 'Secrets Management Policy',
            'description': '''This policy establishes requirements for managing secrets at {{ORGANIZATION_NAME}}.

## I. Overview

{{ORGANIZATION_NAME}} protects secrets including passwords, API keys, certificates, and tokens.

## II. Purpose

To ensure secrets are securely stored, accessed, and rotated.

## III. Scope

All secrets used in applications, infrastructure, and operations.

## IV. Policy

### A. Secrets Storage

1. Centralized secrets management platform
2. Encryption at rest
3. Access logging
4. No secrets in code repositories

### B. Access Control

1. Principle of least privilege
2. Application identity-based access
3. Temporary credentials preferred
4. Human access audited

### C. Secret Types

| Type | Storage | Rotation |
|------|---------|----------|
| Database passwords | Vault | 30 days |
| API keys | Vault | 90 days |
| TLS certificates | Vault | 1 year |
| SSH keys | Vault | 90 days |

### D. Rotation

1. Automated rotation where possible
2. Rotation procedures documented
3. Zero-downtime rotation
4. Rotation verification

### E. Incident Response

1. Immediate revocation capability
2. Exposure detection
3. Impact assessment
4. Rotation on compromise

## V. Compliance

Supports PCI DSS, SOC 2, NIST guidelines.
''',
        },
        'credential-management-policy': {
            'title': 'Credential Management Policy',
            'description': '''This policy establishes requirements for credential management.

## I. Overview

{{ORGANIZATION_NAME}} manages credentials securely throughout their lifecycle.

## II. Purpose

To protect credentials from unauthorized access and misuse.

## III. Scope

All credentials including user accounts, service accounts, and system credentials.

## IV. Policy

### A. User Credentials

1. Strong password requirements
2. Multi-factor authentication
3. Single sign-on where possible
4. Regular password changes

### B. Service Accounts

1. Dedicated service accounts per application
2. Limited permissions
3. Documented ownership
4. Regular review

### C. Privileged Credentials

1. Privileged access management
2. Session recording
3. Just-in-time access
4. Regular rotation

### D. Credential Handling

1. No credential sharing
2. No credentials in email
3. Secure credential transmission
4. Credential masking in logs

## V. Compliance

Supports NIST 800-63, PCI DSS.
''',
        },
    },
}

# Additional categories (simplified for space)
ADDITIONAL_CATEGORIES = {
    'container-security': {
        'container-security-policy': 'Container Security Policy',
        'kubernetes-security-policy': 'Kubernetes Security Policy',
        'image-security-policy': 'Image Security Policy',
    },
    'pam': {
        'privileged-access-management-policy': 'Privileged Access Management Policy',
        'identity-governance-policy': 'Identity Governance Policy',
        'just-in-time-access-policy': 'Just-in-Time Access Policy',
    },
    'insider-threat': {
        'insider-threat-policy': 'Insider Threat Policy',
        'user-behavior-analytics-policy': 'User Behavior Analytics Policy',
    },
    'data-sovereignty': {
        'data-sovereignty-policy': 'Data Sovereignty Policy',
        'cross-border-data-transfer-policy': 'Cross-Border Data Transfer Policy',
        'data-localization-policy': 'Data Localization Policy',
    },
    'vulnerability-disclosure': {
        'vulnerability-disclosure-policy': 'Vulnerability Disclosure Policy',
        'bug-bounty-policy': 'Bug Bounty Policy',
        'coordinated-disclosure-procedure': 'Coordinated Disclosure Procedure',
    },
    'executive-governance': {
        'executive-cybersecurity-governance-policy': 'Executive Cybersecurity Governance Policy',
        'board-cyber-oversight-policy': 'Board Cyber Oversight Policy',
        'ciso-reporting-policy': 'CISO Reporting Policy',
    },
    'shadow-it': {
        'shadow-it-policy': 'Shadow IT Policy',
        'saas-governance-policy': 'SaaS Governance Policy',
        'unapproved-technology-policy': 'Unapproved Technology Policy',
    },
    'iot-ot-security': {
        'iot-security-policy': 'IoT Security Policy',
        'ot-security-policy': 'OT Security Policy',
        'industrial-control-systems-policy': 'Industrial Control Systems Policy',
    },
}


def create_policy_template(policy_id, title, category, content=None):
    """Create a policy template with YAML frontmatter"""
    today = datetime.now().strftime('%Y-%m-%d')

    if content is None:
        content = f'''This policy establishes requirements for {title.lower().replace(' policy', '')} at {{{{ORGANIZATION_NAME}}}}.

## I. Overview

{{{{ORGANIZATION_NAME}}}} implements this policy to ensure appropriate controls and governance.

## II. Purpose

To establish standards and procedures for {title.lower().replace(' policy', '')}.

## III. Scope

This policy applies to all {{{{ORGANIZATION_NAME}}}} personnel, systems, and processes.

## IV. Policy

### A. General Requirements

1. [ACTION REQUIRED: Define specific requirements]
2. [ACTION REQUIRED: Specify controls]
3. [ACTION REQUIRED: Document procedures]

### B. Implementation

1. [ACTION REQUIRED: Define implementation steps]
2. [ACTION REQUIRED: Specify roles and responsibilities]

## V. Compliance

This policy supports compliance with applicable frameworks and regulations.

## VI. Enforcement

Violations of this policy may result in disciplinary action.

## VII. Distribution

This policy shall be distributed to all applicable personnel.
'''

    policy_type = 'procedure' if 'procedure' in policy_id else 'policy'

    frontmatter = f'''---
id: {policy_id}
title: {title}
version: 1.0.0
category: {category}
type: {policy_type}
status: active
frameworks: {{}}
references: []
variables:
- ORGANIZATION_NAME
- EFFECTIVE_DATE
- APPROVAL_DATE
conditions: []
requires_customization:
- section: "IV.A"
  reason: "Requires organization-specific requirements"
  frameworks: []
  priority: high
organization_tiers:
- medium
- enterprise
industries: []
created: '{today}'
last_reviewed: null
next_review: null
author: Policy Committee
approver: null
---

{content}'''

    return frontmatter


def main():
    project_dir = Path(__file__).parent.parent
    policies_dir = project_dir / 'policies'

    created = 0

    # Create policies with full content
    for category, policies in NEW_POLICIES.items():
        category_dir = policies_dir / category
        category_dir.mkdir(exist_ok=True)

        for policy_id, policy_data in policies.items():
            filepath = category_dir / f'{policy_id}.md'
            content = create_policy_template(
                policy_id,
                policy_data['title'],
                category,
                policy_data['description']
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f'[OK] {filepath}')
            created += 1

    # Create stub policies for additional categories
    for category, policies in ADDITIONAL_CATEGORIES.items():
        category_dir = policies_dir / category
        category_dir.mkdir(exist_ok=True)

        for policy_id, title in policies.items():
            filepath = category_dir / f'{policy_id}.md'
            content = create_policy_template(policy_id, title, category)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f'[OK] {filepath}')
            created += 1

    print()
    print(f'Created {created} new policy templates')


if __name__ == '__main__':
    main()
