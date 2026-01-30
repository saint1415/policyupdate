---
id: business-impact-analysis
title: Business Impact Analysis
version: 1.0.0
category: business-continuity
type: policy
status: active
frameworks:
  hipaa:
  - 164.308.a.7.ii.E
  soc2:
  - CC9.1
references:
- business-continuity-plan
- operations-department-plan
variables:
- EFFECTIVE_DATE
- HR_DEPARTMENT
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

## Table of Contents

## I. Introduction	3

## II. Business Processes	5

## III. Financial Impact	6

## IV. Non-Financial Impacts	7

## V. Manual Procedures	8

## VI. Work Area Requirements	9

## VII. Application Software	10

## VIII. Third Party Services	11

## VIII. Information Technology	12

## IX. Summary	14

## I. Introduction

### A. Purpose

This Business Impact Analysis (BIA) helps {{ORGANIZATION_NAME}} (Company) identify the business processes and applications that are essential to the survival of the business.  The Business Impact Analysis identifies the amount of acceptable data loss (recovery point objective) as well as the speed at which systems must be restored (recovery time objective).
Business impacts are identified based on a worst-case scenario assuming that the infrastructure supporting each department has been destroyed and all records, equipment, etc. are not immediately accessible.  This Business Impact Analysis does not address recovery as these issues are addressed in the Business Continuity Plan and supporting documents.
This Business Impact Analysis (BIA) identifies mission critical business functions and associated critical resources.  Determining critical business functions and the impact on the organization is the first step in business continuity.  This Business Impact Analysis:
Identifies important business processes
Determines processes critical to the business
Estimates the potential impact and recovery timeframes
Prioritizes critical processes
During this process, the following were addressed:
The systems and services important to the business
The length of time Company can tolerate a business disruption
The amount of information loss that can be tolerated
The cost to the business in terms of losses to key systems or services

### B. Scope

Our scope included an assessment and analysis of Company’s business processes.  To gather this information we used a questionnaire and interview process that asked a series of questions for each business unit area.  After information was gathered from each business area, it was assembled and analyzed, and a prioritized list of systems and services was created.
The questionnaire and interview identified key sources of information and other resources for the organization.  The intent was to identify:
The financial impact resulting from the loss of a business function
The non-financial impact due to an outage
Critical points and resources required by various business functions
Computer software applications
Impact resulting from lost transactions/data
Interfaces with external business partners

### C. Supporting Information

Interviews with the following departments provided supporting information for this Business Impact Analysis:
Accounting and Finance
Customer Service
{{HR_DEPARTMENT}}
Legal
Marketing
Production and Operations
Sales

## II. Business Processes

### A. Overview

By interviewing key staff members, the Business Impact Analysis identified important business processes and associated critical resources.  The process:
Identified how quickly essential business units and/or processes needed to return to full operation following a disaster situation
Identified the resources required to resume business operations
Business impacts were identified based on worst-case scenario that assumed that the physical infrastructure supporting each respective business unit had been destroyed and all records, equipment, etc. were not accessible for a range of time periods.

### B. Importance

Through interviews with the organization’s staff, important business processes were identified.  The importance of the business processes were classified according to its impact on the organization should the business process not be allowed to perform its service due to a business disruption.  The following table summarizes the results of the interviews:
The above table provides a high-level overview of business processes provided by various departments.  The time listed when the issue becomes a High priority is based upon either the department’s inability to provide service or a high cost associated with the loss of the business process.

## III. Financial Impact

### A. Overview

The financial impact evaluated the loss to the department in the event of a disaster that resulted in the loss of a business process.  Financial impact included various costs including:
Lost Revenue: The loss of this business process resulted in lost revenue.  This included the loss of customer revenue, missed collections, interest, etc.
Penalties: The loss of this business process resulted in fines, penalties, or legal fees due to regulatory requirements (Federal, State, Local, etc.), change in credit rating, etc.
One-time expense: The loss of this business process resulted in one-time expenses including equipment, service provider, materials, etc.
Service: A cost associated with maintaining service to the department’s internal and external customers including temporary staff, overtime, etc.
Recovery of lost transactions: Costs associated with re-creating transactions not available on backup media.  In general, the event occurred after the last backup was stored off site.  Costs included overtime, contracted third party, etc.
Backlog: Overtime or additional staff required for the business process to address the backlog once the business process is restored.

### B. Financial Implications

The table below provides a high-level summary of the financial costs to the organization should a business process not be able to provide services to its internal and external customers.

## IV. Non-Financial Impacts

### A. Overview

Company’s business processes may have non-financial implications should a department be unable to provide services to its internal and external customers.  Non-financial implications include:
Legal ramifications or contractual agreements
Quality of service to clients
Loss of market share
Fines, penalties, litigation
Regulatory compliance
Negative impact on personnel
Other

### B. Non-financial Implications

The table below provides a high-level summary of the non-financial implications to Company should a department not be able to provide services.  Business implications were obtained during interviews with the department representatives.

## V. Manual Procedures

### A. Overview

The Business Impact Analysis interviewed business representatives to determine if departments had documented manual procedures that could be used as ‘workarounds’ in the event IT services were interrupted.  Manual procedures can often be used by departments during short-term outages.  Extended outages rely on our organization’s Business Continuity Plan to resume business operations.

### B. Business Continuity

The table below provides a high-level summary of departments with manual procedures that can be used during short-term business disruptions.  Longer term disruptions may require activating the Business Continuity Plan.
Issues addressed included:
Does your business function have documented manual procedures that could be used as ‘workarounds’ in the event IT services are interrupted? If so, are they stored off-site?  When were the manual procedures tested or last used?
If no manual procedures exist for your business function, estimate the number of workdays it would take to develop them.
Most departments have informal workaround procedures if IT related services (data, phones, Internet, etc.) are not available.  Departments providing important services should complete a Business Continuity of Operations Department Plan.

## VI. Work Area Requirements

### A. Overview

This Business Impact Analysis included the support requirements (space, furniture,  equipment, etc.) for departments in the event of an interruption in normal business operations (loss of facility, loss of IT processing etc.).

### B. Department Requirements

The table below provides a high-level summary of specific department requirements during a business disruption.  Issues addressed included:
The minimum number of employees required (critical personnel) to keep the business function operational to the point that the impact on the organization is minimal during a prolonged outage.
In addition to employee requirements, there may also be unique work area business function resources (forms, contact lists, etc.) required at time of a disaster
Each employee is assumed to require:
Desk
Computer
Phone
Printer
Internet access
Email access

## VII. Application Software

### A. Overview

The Business Impact Analysis identified software applications required by departments to complete their business processes.  Each employee was assumed to require Internet and e-mail access.

### B. Recovery Time and Recovery Point Objectives

The table below provides a high-level summary of specific department requirements during a business disruption.  Issues addressed included:
Importance - High: high cost associated, must be recovered within a short period of time.  Medium: medium to little cost associated, must be recovered.  Recovery does not need to be immediate.  Low: no stated cost, low visibility and can wait for recovery.
Recovery time objective - the number of days or hours the business function can continue to function in an emergency mode without access to this application.  It includes the overall time frame within which the business function or application system must be restored following the declaration of a disaster.
Recovery point objective – the number of hours or days that users spent recreating or reentering lost data.  The data can be re-entered based on source documents, or information from other sources.  The recovery point objective dictates a backup strategy.

## VIII. Third Party Services

### A. Overview

The Business Impact Analysis identified third party service providers required by departments to complete their business processes.  Each employee was assumed to require telephone and Internet access.

### B. Recovery Time and Recovery Point Objectives

The table below provides a high-level summary of third party service providers used by Company’s user departments.  Issues addressed included:
Importance - High: high cost associated, must be recovered within a short period of time.  Medium: medium to little cost associated, must be recovered.  Recovery does not need to be immediate.  Low: no stated cost, low visibility and can wait for recovery.
Recovery time objective - the number of days or hours the business function can continue to function in an emergency mode without access to this service provider.  It includes the overall time frame within which the third party service provider must restore services following their declaration of a disaster.
Recovery point objective – the number of hours or days that the data can be recreated following the loss of the service provider.  The data can be re-entered based on source documents, or information from other sources.  The recovery point objective dictates a backup strategy.  The recovery point objective can vary from a business day to a month.

## VIII. Information Technology

### A. Overview

The Information Technology department provides application systems and technology required to support the organization’s business processes.  This includes application servers, e-mail servers, print servers, phone systems, and network services.

### B. Recovery Time and Recovery Point Objectives

The following table provides a detailed list of the software applications and services available to Company’s users.  The IT priority column represents IT’s understanding of the importance of the application or service.
Software applications
Important Third Party Service Providers (Internet, backup service, maintenance, consultants)

## IX. Summary

### A. Overview

Risk can never be totally eliminated, but can be mitigated by the application of this Business Impact Analysis and Business Continuity Plan.  The decision as to what level risk is acceptable is based on management’s review of the residual risk that exists after controls have been implemented to reduce risks to acceptable levels.
This Business Impact Analysis provides management with an analysis of the financial and non-financial impact of a business disruption on various departments.  Since the cost of providing redundant and fault tolerance IT solutions can be significant, it is important that management knows the impact of a business disruption on user departments.

### B. IT Alignment

IT seems to be aligned with the needs of the users.  The table below compares IT’s time to restore availability against the needs of the users.
Company’s agreements with the following external service providers should be reviewed to ensure service levels and uptime are stated and are aligned with user department requirements.

### C. Department Responsibilities

IT should implement the following tiered approach to business continuity:
While the organization is vulnerable to business disruptions, most departments can continue some level of functionality even with highly diminished IT support.  Based on the interviews, the vast majority of employees are aware of the issues surrounding business continuity.
User departments should:
Resources - ensure that any special forms (checks, etc.) are stored off-site and are available in an emergency.
Equipment - ensure that special equipment such as scanners, scanner software, etc. are available.
Procedures – develop workaround procedures to maintain business processes in the event of IT service disruptions including loss of access to software applications, inability to access the Internet, phones not working, etc.