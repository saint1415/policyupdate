# PolicyUpdate API Reference

## Overview

The PolicyUpdate API provides programmatic access to all platform features. It follows REST conventions and returns JSON responses.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most endpoints require authentication. Use session-based authentication via the login endpoint.

### Login

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your-password
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "abc123",
    "username": "admin",
    "role": "admin"
  }
}
```

### Logout

```http
POST /auth/logout
```

---

## Policies

### List Policies

```http
GET /api/policies
```

**Response:**
```json
[
  {
    "id": "access-control-policy",
    "title": "Access Control Policy",
    "category": "access-control",
    "frameworks": ["nist_csf_2.0", "iso_27001_2022", "soc2"]
  }
]
```

### Get Policy Details

```http
GET /api/policies/{policy_id}
```

**Response:**
```json
{
  "id": "access-control-policy",
  "title": "Access Control Policy",
  "category": "access-control",
  "frameworks": {
    "nist_csf_2.0": ["PR.AA-01", "PR.AA-02"],
    "iso_27001_2022": ["A.5.15", "A.5.18"],
    "soc2": ["CC6.1", "CC6.2"]
  },
  "references": ["password-policy", "authentication-policy"],
  "variables": ["ORGANIZATION_NAME", "CSO_TITLE"],
  "content_preview": "## I. Overview\n\n{{ORGANIZATION_NAME}} establishes..."
}
```

### Search Policies

```http
GET /api/policies/search?q={query}
```

**Parameters:**
- `q` (required): Search query

**Response:**
```json
[
  {
    "id": "incident-response-policy",
    "title": "Incident Response Policy",
    "category": "incident-response"
  }
]
```

---

## Frameworks

### List Frameworks

```http
GET /api/frameworks
```

**Response:**
```json
[
  {
    "id": "soc2",
    "name": "SOC 2 Type II",
    "version": "2017",
    "controls": 56,
    "required_policies": 56
  }
]
```

### Get Framework Details

```http
GET /api/frameworks/{framework_id}
```

**Response:**
```json
{
  "id": "soc2",
  "name": "SOC 2 Type II",
  "version": "2017",
  "controls": 56,
  "required_policies": 56,
  "recommended_policies": 12,
  "control_list": [
    {"id": "CC1.1", "name": "COSO Principle 1", "category": "common-criteria"}
  ]
}
```

### Get Framework Coverage

```http
GET /api/frameworks/{framework_id}/coverage
```

**Response:**
```json
{
  "framework_id": "soc2",
  "framework_name": "SOC 2 Type II",
  "total_controls": 56,
  "fully_covered": 56,
  "partially_covered": 0,
  "not_covered": 0,
  "coverage_percentage": 100.0,
  "missing_policies": []
}
```

---

## Clients

### List Clients

```http
GET /api/clients
```

**Response:**
```json
[
  {
    "id": "abc123",
    "name": "Acme Corporation",
    "industry": "technology",
    "size_tier": "medium",
    "frameworks": ["soc2", "hipaa"]
  }
]
```

### Create Client

```http
POST /api/clients
Content-Type: application/json

{
  "name": "Acme Corporation",
  "industry": "technology",
  "size_tier": "medium",
  "frameworks": ["soc2", "hipaa"]
}
```

**Response:**
```json
{
  "id": "abc123",
  "name": "Acme Corporation",
  "message": "Client created successfully"
}
```

### Get Client Details

```http
GET /api/clients/{client_id}
```

**Response:**
```json
{
  "client": {
    "id": "abc123",
    "name": "Acme Corporation",
    "industry": "technology",
    "size_tier": "medium",
    "employee_count": 250,
    "target_frameworks": ["soc2", "hipaa"],
    "variables": {
      "ORGANIZATION_NAME": "Acme Corporation",
      "CSO_TITLE": "CISO"
    }
  },
  "generations": {
    "total": 5,
    "total_policies_generated": 280,
    "latest": "2024-01-15T10:30:00"
  },
  "compliance": {
    "frameworks_tracked": 2,
    "compliant": 1,
    "partial": 1,
    "non_compliant": 0
  }
}
```

### Delete Client

```http
DELETE /api/clients/{client_id}
```

**Response:**
```json
{
  "message": "Client deleted"
}
```

---

## Generation

### Generate Package

```http
POST /api/generate
Content-Type: application/json

{
  "client_name": "Acme Corporation",
  "org_name": "Acme Corporation",
  "cso_title": "Chief Information Security Officer",
  "frameworks": ["soc2", "hipaa"],
  "format": "docx"
}
```

**Parameters:**
- `client_name` (required): Name of the client
- `org_name` (optional): Organization name for variable substitution
- `cso_title` (optional): CSO title for variable substitution
- `frameworks` (optional): Array of framework IDs
- `format` (optional): Output format (docx, pdf, html, all)

**Response:**
```json
{
  "client_name": "Acme Corporation",
  "total_policies": 85,
  "incomplete_count": 3,
  "frameworks": ["soc2", "hipaa"],
  "files": [
    {
      "format": "docx",
      "filename": "acme_corporation_20240115.docx",
      "path": "/app/output/acme_corporation_20240115.docx"
    }
  ]
}
```

### Download File

```http
GET /api/download/{filename}
```

**Response:** Binary file download

---

## Monitoring

### List Feeds

```http
GET /api/monitor/feeds
```

**Response:**
```json
[
  {
    "id": "nist-csrc",
    "name": "NIST CSRC News",
    "url": "https://csrc.nist.gov/news/rss",
    "type": "rss",
    "keywords": ["CSF", "800-53", "cybersecurity"],
    "frameworks": ["nist_csf_2.0", "nist_800_53"],
    "enabled": true
  }
]
```

### Get Recent Items

```http
GET /api/monitor/recent?days={days}
```

**Parameters:**
- `days` (optional): Number of days to look back (default: 7)

**Response:**
```json
[
  {
    "id": "item123",
    "feed_id": "nist-csrc",
    "title": "NIST Releases Updated Cybersecurity Framework",
    "link": "https://nist.gov/...",
    "summary": "NIST has released...",
    "published": "2024-01-15T09:00:00",
    "relevance": 0.85,
    "frameworks": ["nist_csf_2.0"]
  }
]
```

---

## Users (Admin Only)

### List Users

```http
GET /auth/api/users
```

**Response:**
```json
[
  {
    "id": "user123",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "last_login": "2024-01-15T10:00:00"
  }
]
```

### Create User

```http
POST /auth/api/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "role": "analyst"
}
```

**Response:**
```json
{
  "id": "user456",
  "username": "newuser",
  "message": "User created successfully"
}
```

### Delete User

```http
DELETE /auth/api/users/{user_id}
```

**Response:**
```json
{
  "message": "User deleted"
}
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting

The API implements rate limiting:
- **100 requests per minute** for authenticated users
- **20 requests per minute** for unauthenticated requests

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320000
```

---

## Python SDK Example

```python
import requests

class PolicyUpdateClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.session = requests.Session()
        self._login(username, password)

    def _login(self, username, password):
        self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )

    def list_policies(self):
        return self.session.get(f"{self.base_url}/api/policies").json()

    def generate_package(self, client_name, frameworks, format="docx"):
        return self.session.post(
            f"{self.base_url}/api/generate",
            json={
                "client_name": client_name,
                "frameworks": frameworks,
                "format": format
            }
        ).json()

# Usage
client = PolicyUpdateClient("http://localhost:5000", "admin", "password")
policies = client.list_policies()
result = client.generate_package("Acme Corp", ["soc2", "hipaa"])
```

---

## Webhook Notifications

Configure webhook notifications for monitoring alerts:

### Slack Payload

```json
{
  "attachments": [{
    "color": "#fd7e14",
    "title": "[HIGH] NIST CSF 2.0 Update",
    "text": "NIST has released updated guidance...",
    "footer": "PolicyUpdate | change_detector",
    "ts": 1705320000
  }]
}
```

### Microsoft Teams Payload

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "fd7e14",
  "summary": "[HIGH] NIST CSF 2.0 Update",
  "sections": [{
    "activityTitle": "[HIGH] NIST CSF 2.0 Update",
    "text": "NIST has released updated guidance...",
    "facts": [
      {"name": "Severity", "value": "HIGH"},
      {"name": "Source", "value": "change_detector"}
    ]
  }]
}
```

### Generic Webhook Payload

```json
{
  "id": "alert_abc123",
  "title": "[HIGH] NIST CSF 2.0 Update",
  "message": "NIST has released updated guidance...",
  "severity": "high",
  "timestamp": "2024-01-15T10:00:00",
  "source": "change_detector",
  "metadata": {
    "frameworks": ["nist_csf_2.0"],
    "policies_affected": 15
  }
}
```

---

*API Version: 1.0*
*Last Updated: January 2026*
