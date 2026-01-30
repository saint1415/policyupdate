---
id: cicd-security-policy
title: CI/CD Security Policy
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

This policy establishes security requirements for CI/CD pipelines.

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
