---
id: network-documentation-policy
title: Network Documentation Policy
version: 1.0.0
category: network-security
type: policy
status: active
frameworks:
  nist_csf_2.0:
  - ID.AM-03
references:
- network-documentation-policy
variables:
- IT_STAFF
- ORGANIZATION_NAME
conditions: []
requires_customization: []
organization_tiers:
- small
- medium
- enterprise
industries: []
created: '2026-01-30'
last_reviewed: null
next_review: null
author: Policy Committee
approver: null
---

## I. Overview

Networks are critical to the business operations of {{ORGANIZATION_NAME}}.  Network documentation helps {{ORGANIZATION_NAME}} adhere to industry best practices, reduces downtime and makes the troubleshooting process more efficient when problems arise.

## II. Purpose

This policy details the aspects of the network that need to be documented, especially each server.  This policy also communicates to each system administrator exactly what is expected regarding the documentation process.

## III. Scope

This policy applies to system administrators at {{ORGANIZATION_NAME}}.  This policy applies whether the equipment is owned or leased by {{ORGANIZATION_NAME}}.

## IV. Policy

The network structure and configuration shall be documented with a map of the network's topology including:
Each network segment
Gateways
Routers
Firewalls
Servers
While the information included in a network topology diagram is not necessarily specific, there is certain information that must be included for each server, even if that information has to be placed in an appendix.  For each server, documentation shall include the server's name, its IP address and the role that the server is performing (DNS, DHCP, mail server, etc.).  Documentation shall describe situations where the servers have multiple IP addresses or network interface cards.
An Information Systems Log Form shall be maintained as a part of the network documentation.  This form shall detail changes such as patch and application installations, modified security settings, system maintenance, backups, and errors.
Software applications, versions, and manufacturer contact information shall be provided as a part of the network documentation.  Documentation shall include software applications and their versions running on each server.  Copies of the software licenses shall be retained in hardcopy or electronic format.
Documentation shall include network components such as switches, routers, gateways and other networking hardware.  As appropriate, the documentation shall include:
How the device is connected to the network
How the device is configured
Configuration backups
Firmware revision
Document Active Directory
Domain names in the forest
Active Directory site structure
Where servers exist within the Active Directory hierarchy
The location and contents of each group policy
Any external trusts that may exist
The backup methodology shall be documented and include backup software used, version, backup media, rotation schedule, off-site storage, where media is stored, etc.  See the Backup Policy and Backup Plan for more information.
Network Infrastructure and related system documentation shall be protected against unauthorized access but shall be made available to those who need it to perform their duties.

## V. Enforcement

Any Staff found to have violated this policy may be subject to disciplinary action, up to and including termination.

## VI. Distribution

This policy is to be distributed to all {{ORGANIZATION_NAME}} {{IT_STAFF}}.
Policy History
References:
COBIT APO01.02-03, APO05.05, APO11.09-10, APO12.02, APO12.07, APO13.07, BAI11.09
GDPR Article 25
HIPAA 164.316(b)(1)
ISO 27001:2013 5.2, 6.1.2, 6.2, 7.2, 7.5, 8.1, 9.1
NIST SP 800-37 3.2, 3.4
NIST SP 800-53 CM-8, PM-5, RA-1, SA-5
NIST Cybersecurity Framework ID.RA-1, ID.RA-3, PR.PT-1, RS.MI-3
PCI 1.1, 1.5, 2.4-5, 3.5 -7, 4.3, 5.4