---
id: supply-chain-security-policy
title: Supply Chain Security Policy
version: 1.0.0
category: supply-chain
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

This policy establishes requirements for securing the supply chain at {{ORGANIZATION_NAME}}.

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
