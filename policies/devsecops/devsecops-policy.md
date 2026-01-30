---
id: devsecops-policy
title: DevSecOps Policy
version: 1.0.0
category: devsecops
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

This policy establishes DevSecOps practices at {{ORGANIZATION_NAME}}.

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
