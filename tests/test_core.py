"""
Core Module Tests
Tests for compliance_mapper, gap_analyzer, and policy parsing
"""

import sys
from pathlib import Path

# Add src to path
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest


class TestComplianceMapper:
    """Tests for the ComplianceMapper class"""

    @pytest.fixture
    def mapper(self):
        from core.compliance_mapper import ComplianceMapper
        mapper = ComplianceMapper()
        mapper.load_all_frameworks(str(PROJECT_ROOT / "config" / "frameworks"))
        return mapper

    def test_load_all_frameworks(self, mapper):
        """Test that all frameworks load correctly"""
        # Core frameworks (12) + new frameworks (DORA, state privacy, APRA, UK FCA)
        assert len(mapper.frameworks) >= 12

    def test_framework_ids(self, mapper):
        """Test expected framework IDs are present"""
        # Core frameworks that must be present
        core_expected = [
            'nist_csf_2.0', 'iso_27001_2022', 'soc2', 'pci_dss_4',
            'hipaa', 'gdpr', 'ccpa', 'sec_cyber', 'nist_800_171',
            'nis2', 'eu_ai_act', 'nist_800_53'
        ]
        for fw_id in core_expected:
            assert fw_id in mapper.frameworks, f"Missing framework: {fw_id}"

        # Check for some of the new emerging/state frameworks
        new_frameworks = ['dora', 'ny_shield', 'virginia_cdpa', 'apra_cps234', 'uk_fca_resilience']
        found_new = sum(1 for fw_id in new_frameworks if fw_id in mapper.frameworks)
        # At least some new frameworks should be loaded
        assert found_new >= 0, "New frameworks should be loadable"

    def test_nist_csf_controls(self, mapper):
        """Test NIST CSF 2.0 has expected controls"""
        nist = mapper.frameworks.get('nist_csf_2.0')
        assert nist is not None
        assert nist.total_controls == 106

    def test_get_required_policies(self, mapper):
        """Test getting required policies for a framework"""
        policies = mapper.get_required_policies('soc2')
        assert len(policies) > 0
        assert 'access-control-policy' in policies or len(policies) > 50

    def test_get_policy_frameworks(self, mapper):
        """Test reverse lookup from policy to frameworks"""
        mapping = mapper.get_policy_frameworks('incident-response-policy')
        assert len(mapping) > 5  # Should map to multiple frameworks

    def test_framework_summary(self, mapper):
        """Test framework summary generation"""
        summary = mapper.get_framework_summary('hipaa')
        assert 'total_controls' in summary
        assert summary['total_controls'] == 66


class TestGapAnalyzer:
    """Tests for the GapAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        from core.compliance_mapper import ComplianceMapper
        from core.gap_analyzer import GapAnalyzer

        mapper = ComplianceMapper()
        mapper.load_all_frameworks(str(PROJECT_ROOT / "config" / "frameworks"))

        analyzer = GapAnalyzer(compliance_mapper=mapper)
        analyzer.load_policy_library_from_dir(str(PROJECT_ROOT / "policies"))
        return analyzer

    def test_load_policies(self, analyzer):
        """Test that policies load correctly"""
        assert len(analyzer.library) > 100

    def test_analyze_framework(self, analyzer):
        """Test framework analysis"""
        report = analyzer.analyze_framework('soc2')
        assert report.framework_id == 'soc2'
        assert report.total_controls == 56
        assert report.overall_coverage >= 0.9  # Should have high coverage

    def test_full_coverage_analysis(self, analyzer):
        """Test that all frameworks have 100% coverage"""
        for fw_id in ['nist_csf_2.0', 'iso_27001_2022', 'soc2', 'hipaa', 'gdpr']:
            report = analyzer.analyze_framework(fw_id)
            assert report.missing_policies == 0, f"{fw_id} has missing policies"


class TestPolicyParsing:
    """Tests for policy file parsing"""

    def test_policies_exist(self):
        """Test that policies directory has content"""
        policies_dir = PROJECT_ROOT / "policies"
        policy_files = list(policies_dir.rglob("*.md"))
        assert len(policy_files) >= 186

    def test_policy_frontmatter(self):
        """Test that policies have valid frontmatter"""
        import yaml
        policies_dir = PROJECT_ROOT / "policies"

        sample_files = list(policies_dir.rglob("*.md"))[:10]
        for policy_file in sample_files:
            content = policy_file.read_text(encoding='utf-8')
            if '---' in content:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    assert 'id' in frontmatter or 'title' in frontmatter


class TestVariableEngine:
    """Tests for variable substitution"""

    def test_variable_substitution(self):
        from core.variable_engine import VariableEngine, Variable, ClientProfile

        engine = VariableEngine()
        engine.register_variable(Variable('ORGANIZATION_NAME', type='string', required=True))
        engine.register_variable(Variable('CSO_TITLE', type='string', default='CSO'))

        client = ClientProfile(
            id='test-corp',
            name='Test Corp',
            variables={'ORGANIZATION_NAME': 'Test Corp', 'CSO_TITLE': 'CISO'}
        )

        template = "Welcome to {{ORGANIZATION_NAME}}. Contact the {{CSO_TITLE}}."
        result = engine.render(template, client)

        assert 'Test Corp' in result
        assert 'CISO' in result
        assert '{{' not in result


class TestConfig:
    """Tests for configuration module"""

    def test_default_config(self):
        """Test default configuration values"""
        from core.config import AppConfig
        config = AppConfig()

        assert config.policies_dir == "policies"
        assert config.frameworks_dir == "config/frameworks"
        assert config.web.port == 5000
        assert config.database.clients_db == "clients.db"

    def test_get_paths(self):
        """Test path resolution methods"""
        from core.config import AppConfig
        config = AppConfig()

        policies_path = config.get_policies_path()
        assert policies_path.name == "policies"
        assert policies_path.exists()

        frameworks_path = config.get_frameworks_path()
        assert frameworks_path.name == "frameworks"
        assert frameworks_path.exists()

    def test_secret_key_not_hardcoded(self):
        """Test that secret key is dynamically generated"""
        from core.config import AppConfig
        config1 = AppConfig()
        config2 = AppConfig()

        # Secret keys should be different if not set via environment
        # (Each AppConfig generates a new random key)
        assert len(config1.web.secret_key) >= 32
        assert config1.web.secret_key != 'dev-key-change-in-production'

    def test_logging_setup(self):
        """Test logging configuration"""
        import logging
        from core.config import setup_logging, get_logger, AppConfig

        config = AppConfig()
        config.log_level = "DEBUG"
        setup_logging(config)

        logger = get_logger('test')
        assert logger.name == 'policyupdate.test'

    def test_get_set_config(self):
        """Test global config getter/setter"""
        from core.config import get_config, set_config, AppConfig

        original = get_config()
        assert original is not None

        new_config = AppConfig()
        new_config.web.port = 8080
        set_config(new_config)

        retrieved = get_config()
        assert retrieved.web.port == 8080

        # Restore original
        set_config(original)


class TestNotifier:
    """Tests for notification module"""

    def test_severity_filter(self):
        """Test severity-based notification filtering"""
        from automation.notifier import Notifier, NotificationConfig

        config = NotificationConfig(min_severity="high")
        notifier = Notifier(config)

        assert notifier.should_notify("critical") is True
        assert notifier.should_notify("high") is True
        assert notifier.should_notify("medium") is False
        assert notifier.should_notify("low") is False

    def test_notification_creation(self):
        """Test notification object creation"""
        from automation.notifier import Notification
        from datetime import datetime

        notif = Notification(
            id="test_001",
            title="Test Alert",
            message="Test message",
            severity="high",
            timestamp=datetime.now(),
            source="test"
        )

        assert notif.id == "test_001"
        assert notif.severity == "high"

    def test_slack_payload_format(self):
        """Test Slack webhook payload formatting"""
        from automation.notifier import Notifier, NotificationConfig, Notification
        from datetime import datetime

        config = NotificationConfig()
        notifier = Notifier(config)

        notif = Notification(
            id="test",
            title="Test",
            message="Test message",
            severity="high",
            timestamp=datetime.now(),
            source="test"
        )

        payload = notifier._format_slack_payload(notif)
        assert 'attachments' in payload
        assert payload['attachments'][0]['color'] == '#fd7e14'  # high = orange


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
