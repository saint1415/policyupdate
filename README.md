# PolicyUpdate - GRC Policy Management Platform

A comprehensive Governance, Risk, and Compliance (GRC) platform for managing information security policies and compliance frameworks.

## Features

- **186 Security Policies** - Complete policy library covering all major security domains
- **11 Compliance Frameworks** - NIST CSF 2.0, ISO 27001, SOC 2, PCI DSS, HIPAA, GDPR, CCPA, SEC Cyber, NIST 800-171, NIS2, EU AI Act
- **619 Control Mappings** - Full policy-to-control mapping with 100% coverage
- **Client Management** - Track multiple clients with custom variables
- **Policy Generation** - Generate client-specific policy packages
- **Multiple Export Formats** - DOCX and Markdown export

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# List available frameworks
python src/cli/main.py frameworks list

# Generate a policy package
python src/cli/main.py generate "Acme Corp" --frameworks soc2,hipaa --format docx

# Manage clients
python src/cli/main.py clients add "Acme Corp" --industry technology --frameworks soc2,hipaa
python src/cli/main.py clients list
```

## CLI Commands

### Policy Management
```bash
policy-grc policies list              # List all policies
policy-grc policies search <query>    # Search policies
policy-grc policies validate          # Validate policy library
```

### Framework Analysis
```bash
policy-grc frameworks list            # List compliance frameworks
policy-grc frameworks coverage <fw>   # Show coverage analysis
policy-grc frameworks gaps            # Show cross-framework gaps
```

### Client Management
```bash
policy-grc clients list               # List all clients
policy-grc clients add <name>         # Add new client
policy-grc clients show <id>          # Show client details
policy-grc clients set-var <id> <var> <value>  # Set variable
```

### Generation
```bash
policy-grc generate <client> --frameworks soc2,hipaa --format docx
policy-grc generate <client> --format pdf    # Export to PDF
policy-grc report compliance          # Generate compliance report
```

### Monitoring
```bash
policy-grc monitor setup              # Set up compliance feeds
policy-grc monitor feeds              # List configured feeds
policy-grc monitor check              # Check feeds for updates
policy-grc monitor analyze            # Analyze updates for policy impacts
policy-grc monitor alerts             # Show pending change alerts
policy-grc monitor report             # Generate alert report
```

## Project Structure

```
policyupdate/
├── config/
│   └── frameworks/          # Compliance framework definitions (YAML)
├── policies/                # Policy library (Markdown + YAML frontmatter)
├── src/
│   ├── core/               # Core modules
│   │   ├── compliance_mapper.py
│   │   ├── gap_analyzer.py
│   │   └── policy_parser.py
│   ├── generation/         # Export modules
│   │   ├── package_builder.py
│   │   └── docx_exporter.py
│   ├── crm/               # Client management
│   │   └── client_manager.py
│   └── cli/               # Command-line interface
│       └── main.py
├── data/                   # SQLite database
├── output/                 # Generated packages
└── scripts/               # Utility scripts
```

## Supported Frameworks

| Framework | Controls | Status |
|-----------|----------|--------|
| NIST CSF 2.0 | 106 | 100% Coverage |
| NIST 800-171 Rev 3 | 93 | 100% Coverage |
| ISO 27001:2022 | 93 | 100% Coverage |
| SOC 2 | 56 | 100% Coverage |
| PCI DSS 4.0.1 | 63 | 100% Coverage |
| HIPAA | 66 | 100% Coverage |
| GDPR | 40 | 100% Coverage |
| CCPA/CPRA | 20 | 100% Coverage |
| SEC Cyber Rules | 12 | 100% Coverage |
| NIS2 Directive | 27 | 100% Coverage |
| EU AI Act | 43 | 100% Coverage |

## Policy Categories

34 categories including:
- Access Control
- Network Security
- Business Continuity
- Data Protection
- Incident Response
- Risk Management
- Vendor Management
- AI/ML Governance
- Zero Trust Architecture
- Supply Chain Security
- And 24 more...

## Template Variables

Policies use template variables for customization:

| Variable | Description |
|----------|-------------|
| `{{ORGANIZATION_NAME}}` | Organization name |
| `{{CSO_TITLE}}` | Security officer title |
| `{{EXEC_MGMT}}` | Executive management title |
| `{{EFFECTIVE_DATE}}` | Policy effective date |
| `{{IT_STAFF}}` | IT department name |
| `{{HR_DEPARTMENT}}` | HR department name |
| `{{LEGAL_DEPARTMENT}}` | Legal department name |

## Requirements

- Python 3.10+
- python-docx (for DOCX export)
- PyYAML
- click (for CLI)

## License

Proprietary - For internal use only
