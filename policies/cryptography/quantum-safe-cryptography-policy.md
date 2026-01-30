---
id: quantum-safe-cryptography-policy
title: Quantum-Safe Cryptography Policy
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

This policy establishes requirements for quantum-resistant cryptography at {{ORGANIZATION_NAME}}.

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
