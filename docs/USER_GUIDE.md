# PolicyUpdate User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Web Interface](#web-interface)
5. [Command Line Interface](#command-line-interface)
6. [Client Management](#client-management)
7. [Policy Generation](#policy-generation)
8. [Compliance Frameworks](#compliance-frameworks)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [Administration](#administration)
11. [API Reference](#api-reference)
12. [Troubleshooting](#troubleshooting)

---

## Introduction

PolicyUpdate is a comprehensive GRC (Governance, Risk, Compliance) Policy Management Platform designed for security consultants and organizations. It provides:

- **186 Security Policies** covering all major domains
- **15 Compliance Frameworks** (NIST CSF, ISO 27001, SOC 2, HIPAA, PCI DSS, etc.)
- **Multi-client Management** with CRM capabilities
- **Automated Monitoring** for compliance framework updates
- **Multiple Export Formats** (DOCX, PDF, HTML, Markdown, OSCAL)

### Key Features

| Feature | Description |
|---------|-------------|
| Policy Library | 186 pre-built security policies |
| Compliance Mapping | 900+ controls across 15 frameworks |
| Variable Substitution | Customize policies with client data |
| Gap Analysis | Identify missing policies per framework |
| Audit Logging | Track all user actions |
| Version Control | Policy versioning with diff capability |

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 500MB disk space

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/saint1415/policyupdate.git
cd policyupdate

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:5000
```

### Optional Dependencies

```bash
# For PDF export
pip install weasyprint

# For full web features
pip install flask flask-login gunicorn

# For feed monitoring
pip install feedparser requests

# Install all optional dependencies
pip install -e ".[all]"
```

---

## Quick Start

### 1. Start the Web Interface

```bash
python -m src.web.app
```

Open http://localhost:5000 in your browser.

### 2. Create a Client

```bash
policy-grc clients add "Acme Corporation" \
    --industry technology \
    --size medium \
    --frameworks soc2,hipaa
```

### 3. Set Client Variables

```bash
policy-grc clients set-var "Acme Corporation" ORGANIZATION_NAME "Acme Corporation"
policy-grc clients set-var "Acme Corporation" CSO_TITLE "Chief Information Security Officer"
```

### 4. Generate Policy Package

```bash
policy-grc generate "Acme Corporation" \
    --frameworks soc2,hipaa \
    --format docx \
    --output ./output
```

---

## Web Interface

### Dashboard

The dashboard provides an overview of:
- Total policies in the library
- Number of compliance frameworks
- Client count
- Recent activity

### Policies Browser

Navigate to **Policies** to:
- Browse all 186 policies by category
- Search policies by title or content
- View policy details and framework mappings
- Preview policy content

### Frameworks Viewer

Navigate to **Frameworks** to:
- View all 15 compliance frameworks
- See control counts and policy coverage
- Analyze gaps in your policy library
- Download framework documentation

### Client Management

Navigate to **Clients** to:
- Add new clients
- Configure client variables
- Set target compliance frameworks
- View generation history

### Package Generation

Navigate to **Generate** to:
- Select a client
- Choose target frameworks
- Configure output options
- Generate and download policy packages

---

## Command Line Interface

### Global Options

```bash
policy-grc --version           # Show version
policy-grc --help              # Show help
```

### Policy Commands

```bash
# List all policies
policy-grc policies list

# List policies by category
policy-grc policies list --category access-control

# Search policies
policy-grc policies search "incident response"

# Validate all policies
policy-grc policies validate
```

### Framework Commands

```bash
# List all frameworks
policy-grc frameworks list

# Show framework coverage
policy-grc frameworks coverage soc2

# Show gaps across frameworks
policy-grc frameworks gaps --frameworks soc2,hipaa
```

### Client Commands

```bash
# List all clients
policy-grc clients list

# Add a new client
policy-grc clients add "Client Name" \
    --industry healthcare \
    --size enterprise \
    --frameworks hipaa,soc2

# Show client details
policy-grc clients show "Client Name"

# Set client variable
policy-grc clients set-var "Client Name" ORGANIZATION_NAME "Client Corp"

# Delete a client
policy-grc clients delete "Client Name"
```

### Generation Commands

```bash
# Generate policy package
policy-grc generate "Client Name" \
    --frameworks soc2,hipaa \
    --format docx \
    --output ./output

# Preview without generating (dry-run)
policy-grc generate "Client Name" --frameworks soc2 --dry-run --verbose

# Generate all formats
policy-grc generate "Client Name" --format all
```

### Monitoring Commands

```bash
# Setup default compliance feeds
policy-grc monitor setup

# List configured feeds
policy-grc monitor feeds

# Check for updates
policy-grc monitor check

# View pending alerts
policy-grc monitor alerts

# Acknowledge an alert
policy-grc monitor acknowledge ALERT_ID --notes "Reviewed"

# Generate monitoring report
policy-grc monitor report --output report.md
```

### Bulk Operations

```bash
# Generate for all clients
policy-grc bulk generate --clients all --frameworks soc2

# Generate for specific clients
policy-grc bulk generate --clients client1,client2 --format pdf

# Validate everything
policy-grc bulk validate-all

# Create full backup
policy-grc bulk backup --output ./backups
```

---

## Client Management

### Creating Clients

Clients are organizations that receive policy packages. Each client has:

- **Name**: Organization name
- **Industry**: healthcare, finance, technology, government, etc.
- **Size Tier**: solopreneur, small, medium, enterprise
- **Target Frameworks**: Compliance frameworks they need to meet
- **Variables**: Custom values for policy generation

### Client Variables

| Variable | Description | Example |
|----------|-------------|---------|
| ORGANIZATION_NAME | Full organization name | "Acme Corporation" |
| CSO_TITLE | Security officer title | "Chief Information Security Officer" |
| EXEC_MGMT | Executive management reference | "Executive Leadership Team" |
| IT_STAFF | IT department reference | "Information Technology Department" |
| HR_DEPARTMENT | HR department reference | "Human Resources" |
| LEGAL_DEPARTMENT | Legal department reference | "Legal Affairs" |
| RMO_TITLE | Risk management officer | "Risk Management Director" |
| EFFECTIVE_DATE | Policy effective date | "January 1, 2024" |

### Variable Substitution

Variables in policies appear as `{{VARIABLE_NAME}}`. When generating packages, these are replaced with client-specific values.

---

## Policy Generation

### Output Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| DOCX | .docx | Microsoft Word document |
| PDF | .pdf | Portable Document Format |
| HTML | .html | Standalone HTML file |
| Markdown | .md | Plain text Markdown files |
| OSCAL | .json | Machine-readable OSCAL format |

### Generation Options

- **--frameworks**: Comma-separated framework IDs
- **--format**: Output format (docx, pdf, html, md, all)
- **--output**: Output directory
- **--dry-run**: Preview without creating files
- **--verbose**: Show detailed policy list
- **--all-policies**: Include all policies regardless of framework

### Package Contents

Generated packages include:
1. **Cover Page** - Client name, date, compliance targets
2. **Table of Contents** - Linked policy list
3. **Policies** - Full policy content by category
4. **Customization Checklist** - Items requiring client input
5. **Appendix** - Framework mapping summary

---

## Compliance Frameworks

### Supported Frameworks

| Framework | Controls | Description |
|-----------|----------|-------------|
| NIST CSF 2.0 | 106 | Cybersecurity Framework |
| NIST 800-53 | 202 | Security and Privacy Controls |
| NIST 800-171 | 93 | Protecting CUI |
| ISO 27001:2022 | 93 | Information Security Management |
| SOC 2 | 56 | Service Organization Controls |
| PCI DSS 4.0 | 63 | Payment Card Industry |
| HIPAA | 66 | Healthcare Privacy |
| GDPR | 40 | EU Data Protection |
| CCPA/CPRA | 20 | California Privacy |
| SEC Cyber | 12 | Securities Disclosure |
| NIS2 | 27 | EU Network Security |
| EU AI Act | 43 | AI Regulation |
| CIS Controls v8 | 153 | Critical Security Controls |
| FedRAMP | 156+ | Federal Cloud Security |
| CMMC 2.0 | 110+ | DoD Contractor Security |

### Framework Coverage

Each policy maps to multiple framework controls. The gap analyzer identifies:
- **Fully Covered**: All required policies exist
- **Partially Covered**: Some policies exist
- **Not Covered**: No policies map to control

---

## Monitoring & Alerts

### Feed Monitoring

The system monitors compliance framework updates through:
- RSS feeds from official sources
- Web page change detection
- Keyword-based filtering

### Setting Up Monitoring

```bash
# Load default feeds
policy-grc monitor setup

# Check all feeds
policy-grc monitor check

# View recent items
policy-grc monitor analyze --days 7
```

### Alert Workflow

1. **Detection**: New updates detected from feeds
2. **Analysis**: Impact on existing policies assessed
3. **Alert Creation**: Notifications sent via email/webhook
4. **Review**: Security team reviews alerts
5. **Acknowledgment**: Alert marked as reviewed
6. **Resolution**: Policies updated, alert resolved

### Notification Configuration

Set environment variables:
```bash
POLICYUPDATE_SMTP_HOST=smtp.gmail.com
POLICYUPDATE_SMTP_USER=alerts@company.com
POLICYUPDATE_SMTP_PASSWORD=secret
POLICYUPDATE_EMAIL_FROM=alerts@company.com
POLICYUPDATE_WEBHOOK_URL=https://hooks.slack.com/...
```

---

## Administration

### User Management

The web interface supports role-based access:

| Role | Permissions |
|------|-------------|
| Admin | Full access, user management |
| Manager | Generate, edit clients |
| Analyst | Generate, view |
| Viewer | View only |

### Default Admin Credentials

On first run, check `data/admin_credentials.txt` for the auto-generated admin password. **Change it immediately!**

### Audit Logging

All actions are logged to the audit database:
- Authentication events
- Policy generations
- Client changes
- System configuration

View audit logs:
```bash
policy-grc bulk export-audit --output audit.json --days 90
```

### Backup & Recovery

```bash
# Create backup
policy-grc bulk backup --output ./backups/$(date +%Y%m%d)

# Backups include:
# - SQLite databases (clients, audit, versions)
# - Policy files
# - Framework definitions
```

---

## API Reference

### Authentication

All API endpoints require authentication (except `/auth/login`).

### Endpoints

#### Policies
```
GET  /api/policies              List all policies
GET  /api/policies/<id>         Get policy details
GET  /api/policies/search?q=    Search policies
```

#### Frameworks
```
GET  /api/frameworks            List all frameworks
GET  /api/frameworks/<id>       Get framework details
GET  /api/frameworks/<id>/coverage  Get coverage analysis
```

#### Clients
```
GET    /api/clients             List all clients
POST   /api/clients             Create client
GET    /api/clients/<id>        Get client details
DELETE /api/clients/<id>        Delete client
```

#### Generation
```
POST /api/generate              Generate policy package
GET  /api/download/<filename>   Download generated file
```

#### Monitoring
```
GET  /api/monitor/feeds         List configured feeds
GET  /api/monitor/recent        Get recent feed items
```

### Example API Usage

```python
import requests

# Login
session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'username': 'admin',
    'password': 'your-password'
})

# List policies
policies = session.get('http://localhost:5000/api/policies').json()

# Generate package
result = session.post('http://localhost:5000/api/generate', json={
    'client_name': 'Acme Corp',
    'frameworks': ['soc2', 'hipaa'],
    'format': 'docx'
}).json()
```

---

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'click'"
```bash
pip install click
```

#### "PDF export unavailable"
```bash
pip install weasyprint
# On macOS: brew install pango
# On Ubuntu: apt-get install libpango-1.0-0
```

#### "Permission denied" on output directory
```bash
mkdir -p output
chmod 755 output
```

#### Web interface not starting
```bash
# Check port availability
lsof -i :5000

# Use different port
FLASK_RUN_PORT=8080 python -m src.web.app
```

### Debug Mode

Enable debug logging:
```bash
export POLICYUPDATE_LOG_LEVEL=DEBUG
export POLICYUPDATE_DEBUG=true
python -m src.web.app
```

### Getting Help

- GitHub Issues: https://github.com/saint1415/policyupdate/issues
- Documentation: `docs/` directory
- CLI Help: `policy-grc --help`

---

## Appendix

### Policy Categories

1. Access Control
2. Network Security
3. Data Protection
4. Incident Response
5. Business Continuity
6. Vendor Management
7. Physical Security
8. Personnel Security
9. Compliance & Audit
10. Operations
11. AI & ML Governance
12. Supply Chain Security
13. Zero Trust Architecture
14. Container Security
15. API Security
16. DevSecOps
17. Insider Threat
18. Privacy
19. Risk Management

### Keyboard Shortcuts (Web)

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Search policies |
| Ctrl+G | Go to generate |
| Ctrl+C | Go to clients |
| Esc | Close modal |

---

*PolicyUpdate GRC Platform - Version 1.0*
*Last Updated: January 2026*
