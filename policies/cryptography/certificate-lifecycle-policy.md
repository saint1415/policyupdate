---
id: certificate-lifecycle-policy
title: Certificate Lifecycle Policy
version: 1.0.0
category: cryptography
type: policy
status: active
frameworks: {}
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
created: '2026-01-30'
last_reviewed: null
next_review: null
author: Policy Committee
approver: null
---

This policy establishes requirements for digital certificate management.

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
