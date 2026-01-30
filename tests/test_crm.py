"""
CRM Module Tests
Tests for client management functionality
"""

import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest


class TestClientManager:
    """Tests for the ClientManager class"""

    @pytest.fixture
    def manager(self, tmp_path):
        from crm.client_manager import ClientManager
        db_path = tmp_path / "test_clients.db"
        return ClientManager(str(db_path))

    def test_create_client(self, manager):
        """Test creating a new client"""
        client = manager.create_client(
            "Test Company",
            industry="technology",
            size_tier="medium",
            target_frameworks=["soc2", "hipaa"]
        )

        assert client.name == "Test Company"
        assert client.industry == "technology"
        assert client.size_tier == "medium"
        assert "soc2" in client.target_frameworks

    def test_get_client(self, manager):
        """Test retrieving a client"""
        created = manager.create_client("Retrieve Test")
        retrieved = manager.get_client(created.id)

        assert retrieved is not None
        assert retrieved.name == "Retrieve Test"

    def test_get_client_by_name(self, manager):
        """Test retrieving client by name"""
        manager.create_client("Name Lookup Test")
        client = manager.get_client_by_name("Name Lookup Test")

        assert client is not None
        assert client.name == "Name Lookup Test"

    def test_update_client(self, manager):
        """Test updating client details"""
        client = manager.create_client("Update Test")
        manager.update_client(
            client.id,
            industry="healthcare",
            size_tier="enterprise"
        )

        updated = manager.get_client(client.id)
        assert updated.industry == "healthcare"
        assert updated.size_tier == "enterprise"

    def test_update_variables(self, manager):
        """Test updating client variables"""
        client = manager.create_client("Variables Test")
        manager.update_client(
            client.id,
            variables={
                "ORGANIZATION_NAME": "Variables Test Corp",
                "CSO_TITLE": "VP Security"
            }
        )

        updated = manager.get_client(client.id)
        assert updated.variables.get("ORGANIZATION_NAME") == "Variables Test Corp"
        assert updated.variables.get("CSO_TITLE") == "VP Security"

    def test_delete_client(self, manager):
        """Test deleting a client"""
        client = manager.create_client("Delete Test")
        manager.delete_client(client.id)

        deleted = manager.get_client(client.id)
        assert deleted is None

    def test_list_clients(self, manager):
        """Test listing all clients"""
        manager.create_client("Client A")
        manager.create_client("Client B")
        manager.create_client("Client C")

        clients = manager.list_clients()
        assert len(clients) >= 3

    def test_record_generation(self, manager):
        """Test recording policy generation"""
        client = manager.create_client("Generation Test")
        gen = manager.record_generation(
            client.id,
            policies_count=50,
            frameworks=["soc2", "hipaa"],
            output_format="docx",
            output_path="/tmp/test_output.docx"
        )

        assert gen is not None
        assert gen.id is not None

    def test_update_compliance_status(self, manager):
        """Test updating compliance status"""
        client = manager.create_client("Compliance Test")
        manager.update_compliance_status(
            client.id,
            framework_id="soc2",
            status="partial",
            coverage_percentage=75.5,
            gaps_count=2
        )

        summary = manager.get_client_summary(client.id)
        assert summary["compliance"]["frameworks_tracked"] > 0

    def test_client_summary(self, manager):
        """Test getting client summary"""
        client = manager.create_client(
            "Summary Test",
            industry="finance",
            target_frameworks=["soc2", "pci_dss"]
        )
        manager.record_generation(client.id, 45, ["soc2"], "docx", "/tmp/summary_test.docx")

        summary = manager.get_client_summary(client.id)

        assert "client" in summary
        assert "generations" in summary
        assert "compliance" in summary
        assert summary["client"]["name"] == "Summary Test"
        assert summary["generations"]["total"] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
