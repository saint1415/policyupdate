"""
Client Manager Module
Manages client profiles, policy generations, and compliance tracking
"""

import sqlite3
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Client:
    """Client profile"""
    id: str
    name: str
    industry: str = ""
    size_tier: str = "medium"  # solopreneur, small, medium, enterprise
    employee_count: int = 0
    primary_contact_name: str = ""
    primary_contact_email: str = ""
    target_frameworks: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        return cls(**data)


@dataclass
class PolicyGeneration:
    """Record of a policy package generation"""
    id: str
    client_id: str
    generated_at: str
    policies_count: int
    frameworks: List[str]
    output_format: str
    output_path: str
    incomplete_count: int
    status: str = "complete"  # complete, draft, archived


@dataclass
class ComplianceStatus:
    """Compliance status for a client-framework pair"""
    id: str
    client_id: str
    framework_id: str
    last_assessed: str
    status: str  # compliant, partial, non_compliant, not_assessed
    coverage_percentage: float
    gaps_count: int
    notes: str = ""


class ClientManager:
    """
    Manages client data with SQLite persistence.

    Usage:
        manager = ClientManager("data/clients.db")
        client = manager.create_client("Acme Corp", industry="technology")
        manager.update_client(client.id, variables={"ORGANIZATION_NAME": "Acme"})
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT DEFAULT '',
                size_tier TEXT DEFAULT 'medium',
                employee_count INTEGER DEFAULT 0,
                primary_contact_name TEXT DEFAULT '',
                primary_contact_email TEXT DEFAULT '',
                target_frameworks TEXT DEFAULT '[]',
                variables TEXT DEFAULT '{}',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Policy generations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS policy_generations (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                policies_count INTEGER NOT NULL,
                frameworks TEXT NOT NULL,
                output_format TEXT NOT NULL,
                output_path TEXT NOT NULL,
                incomplete_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'complete',
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        ''')

        # Compliance status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_status (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                framework_id TEXT NOT NULL,
                last_assessed TEXT NOT NULL,
                status TEXT NOT NULL,
                coverage_percentage REAL DEFAULT 0,
                gaps_count INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                FOREIGN KEY (client_id) REFERENCES clients(id),
                UNIQUE(client_id, framework_id)
            )
        ''')

        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # CLIENT MANAGEMENT
    # =========================================================================

    def create_client(self, name: str, **kwargs) -> Client:
        """Create a new client"""
        now = datetime.now().isoformat()
        client = Client(
            id=str(uuid.uuid4())[:8],
            name=name,
            industry=kwargs.get('industry', ''),
            size_tier=kwargs.get('size_tier', 'medium'),
            employee_count=kwargs.get('employee_count', 0),
            primary_contact_name=kwargs.get('primary_contact_name', ''),
            primary_contact_email=kwargs.get('primary_contact_email', ''),
            target_frameworks=kwargs.get('target_frameworks', []),
            variables=kwargs.get('variables', {}),
            notes=kwargs.get('notes', ''),
            created_at=now,
            updated_at=now
        )

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clients (id, name, industry, size_tier, employee_count,
                primary_contact_name, primary_contact_email, target_frameworks,
                variables, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client.id, client.name, client.industry, client.size_tier,
            client.employee_count, client.primary_contact_name,
            client.primary_contact_email, json.dumps(client.target_frameworks),
            json.dumps(client.variables), client.notes,
            client.created_at, client.updated_at
        ))
        conn.commit()
        conn.close()

        return client

    def get_client(self, client_id: str) -> Optional[Client]:
        """Get a client by ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Client(
            id=row['id'],
            name=row['name'],
            industry=row['industry'],
            size_tier=row['size_tier'],
            employee_count=row['employee_count'],
            primary_contact_name=row['primary_contact_name'],
            primary_contact_email=row['primary_contact_email'],
            target_frameworks=json.loads(row['target_frameworks']),
            variables=json.loads(row['variables']),
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def get_client_by_name(self, name: str) -> Optional[Client]:
        """Get a client by name (case-insensitive)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE LOWER(name) = LOWER(?)', (name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self.get_client(row['id'])

    def list_clients(self) -> List[Client]:
        """List all clients"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM clients ORDER BY name')
        rows = cursor.fetchall()
        conn.close()

        return [self.get_client(row['id']) for row in rows]

    def update_client(self, client_id: str, **kwargs) -> Optional[Client]:
        """Update a client"""
        client = self.get_client(client_id)
        if not client:
            return None

        conn = self._get_conn()
        cursor = conn.cursor()

        updates = []
        values = []

        for key, value in kwargs.items():
            if hasattr(client, key):
                if key in ('target_frameworks', 'variables'):
                    value = json.dumps(value)
                updates.append(f"{key} = ?")
                values.append(value)

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(client_id)

            cursor.execute(
                f"UPDATE clients SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()

        conn.close()
        return self.get_client(client_id)

    def delete_client(self, client_id: str) -> bool:
        """Delete a client and all related records"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM compliance_status WHERE client_id = ?', (client_id,))
        cursor.execute('DELETE FROM policy_generations WHERE client_id = ?', (client_id,))
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # =========================================================================
    # POLICY GENERATION TRACKING
    # =========================================================================

    def record_generation(self, client_id: str, policies_count: int,
                          frameworks: List[str], output_format: str,
                          output_path: str, incomplete_count: int = 0) -> PolicyGeneration:
        """Record a policy generation"""
        gen = PolicyGeneration(
            id=str(uuid.uuid4())[:8],
            client_id=client_id,
            generated_at=datetime.now().isoformat(),
            policies_count=policies_count,
            frameworks=frameworks,
            output_format=output_format,
            output_path=output_path,
            incomplete_count=incomplete_count
        )

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO policy_generations (id, client_id, generated_at,
                policies_count, frameworks, output_format, output_path,
                incomplete_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            gen.id, gen.client_id, gen.generated_at, gen.policies_count,
            json.dumps(gen.frameworks), gen.output_format, gen.output_path,
            gen.incomplete_count, gen.status
        ))
        conn.commit()
        conn.close()

        return gen

    def get_client_generations(self, client_id: str) -> List[PolicyGeneration]:
        """Get all generations for a client"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM policy_generations
            WHERE client_id = ?
            ORDER BY generated_at DESC
        ''', (client_id,))
        rows = cursor.fetchall()
        conn.close()

        return [PolicyGeneration(
            id=row['id'],
            client_id=row['client_id'],
            generated_at=row['generated_at'],
            policies_count=row['policies_count'],
            frameworks=json.loads(row['frameworks']),
            output_format=row['output_format'],
            output_path=row['output_path'],
            incomplete_count=row['incomplete_count'],
            status=row['status']
        ) for row in rows]

    # =========================================================================
    # COMPLIANCE STATUS
    # =========================================================================

    def update_compliance_status(self, client_id: str, framework_id: str,
                                  status: str, coverage_percentage: float,
                                  gaps_count: int, notes: str = "") -> ComplianceStatus:
        """Update or create compliance status for a client-framework pair"""
        comp = ComplianceStatus(
            id=str(uuid.uuid4())[:8],
            client_id=client_id,
            framework_id=framework_id,
            last_assessed=datetime.now().isoformat(),
            status=status,
            coverage_percentage=coverage_percentage,
            gaps_count=gaps_count,
            notes=notes
        )

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO compliance_status
                (id, client_id, framework_id, last_assessed, status,
                 coverage_percentage, gaps_count, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comp.id, comp.client_id, comp.framework_id, comp.last_assessed,
            comp.status, comp.coverage_percentage, comp.gaps_count, comp.notes
        ))
        conn.commit()
        conn.close()

        return comp

    def get_client_compliance(self, client_id: str) -> List[ComplianceStatus]:
        """Get all compliance statuses for a client"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM compliance_status
            WHERE client_id = ?
            ORDER BY framework_id
        ''', (client_id,))
        rows = cursor.fetchall()
        conn.close()

        return [ComplianceStatus(
            id=row['id'],
            client_id=row['client_id'],
            framework_id=row['framework_id'],
            last_assessed=row['last_assessed'],
            status=row['status'],
            coverage_percentage=row['coverage_percentage'],
            gaps_count=row['gaps_count'],
            notes=row['notes']
        ) for row in rows]

    # =========================================================================
    # REPORTS
    # =========================================================================

    def get_client_summary(self, client_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a client"""
        client = self.get_client(client_id)
        if not client:
            return {"error": "Client not found"}

        generations = self.get_client_generations(client_id)
        compliance = self.get_client_compliance(client_id)

        return {
            "client": client.to_dict(),
            "generations": {
                "total": len(generations),
                "latest": generations[0].generated_at if generations else None,
                "total_policies_generated": sum(g.policies_count for g in generations)
            },
            "compliance": {
                "frameworks_tracked": len(compliance),
                "compliant": sum(1 for c in compliance if c.status == "compliant"),
                "partial": sum(1 for c in compliance if c.status == "partial"),
                "non_compliant": sum(1 for c in compliance if c.status == "non_compliant")
            }
        }


def main():
    """Test the client manager"""
    import tempfile
    import os

    print("=" * 60)
    print("CLIENT MANAGER TEST")
    print("=" * 60)

    # Use temp database for testing
    db_path = Path(tempfile.gettempdir()) / "test_clients.db"
    if db_path.exists():
        os.remove(db_path)

    manager = ClientManager(str(db_path))

    # Create clients
    print("\nCreating clients...")
    client1 = manager.create_client(
        "Acme Corporation",
        industry="technology",
        size_tier="medium",
        employee_count=250,
        target_frameworks=["soc2", "hipaa"],
        variables={
            "ORGANIZATION_NAME": "Acme Corporation",
            "CSO_TITLE": "CISO"
        }
    )
    print(f"  Created: {client1.name} (ID: {client1.id})")

    client2 = manager.create_client(
        "Beta Healthcare",
        industry="healthcare",
        size_tier="enterprise",
        target_frameworks=["hipaa", "soc2", "nist_800_171"]
    )
    print(f"  Created: {client2.name} (ID: {client2.id})")

    # List clients
    print("\nListing clients:")
    for client in manager.list_clients():
        print(f"  - {client.name}: {client.industry}, {client.target_frameworks}")

    # Record generations
    print("\nRecording policy generations...")
    gen1 = manager.record_generation(
        client1.id, 63, ["soc2", "hipaa"], "docx",
        "/output/acme_policies.docx", incomplete_count=3
    )
    print(f"  Generation {gen1.id}: {gen1.policies_count} policies")

    # Update compliance
    print("\nUpdating compliance status...")
    manager.update_compliance_status(
        client1.id, "soc2", "partial", 85.5, 8,
        "Need to implement MFA controls"
    )
    manager.update_compliance_status(
        client1.id, "hipaa", "compliant", 100.0, 0
    )

    # Get summary
    print("\nClient summary:")
    summary = manager.get_client_summary(client1.id)
    print(f"  Client: {summary['client']['name']}")
    print(f"  Generations: {summary['generations']['total']}")
    print(f"  Compliance: {summary['compliance']}")

    # Cleanup
    os.remove(db_path)
    print(f"\n[OK] Test complete")


if __name__ == "__main__":
    main()
