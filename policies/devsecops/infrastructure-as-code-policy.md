---
id: infrastructure-as-code-policy
title: Infrastructure as Code Policy
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

This policy establishes requirements for Infrastructure as Code (IaC).

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
