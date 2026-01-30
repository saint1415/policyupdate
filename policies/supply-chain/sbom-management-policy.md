---
id: sbom-management-policy
title: SBOM Management Policy
version: 1.0.0
category: supply-chain
type: policy
status: active
frameworks:
  nist_csf_2.0:
  - GV.SC-09
  - ID.AM-02
references: []
variables:
- ORGANIZATION_NAME
- EFFECTIVE_DATE
- APPROVAL_DATE
conditions: []
requires_customization:
- section: IV.A
  reason: Requires organization-specific requirements
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

This policy establishes requirements for Software Bill of Materials (SBOM) management.

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
