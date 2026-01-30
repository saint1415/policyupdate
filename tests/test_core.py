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
        assert len(mapper.frameworks) == 11

    def test_framework_ids(self, mapper):
        """Test expected framework IDs are present"""
        expected = [
            'nist_csf_2.0', 'iso_27001_2022', 'soc2', 'pci_dss_4',
            'hipaa', 'gdpr', 'ccpa', 'sec_cyber', 'nist_800_171',
            'nis2', 'eu_ai_act'
        ]
        for fw_id in expected:
            assert fw_id in mapper.frameworks, f"Missing framework: {fw_id}"

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
        from core.variable_engine import VariableEngine

        engine = VariableEngine()
        engine.set_variable('ORGANIZATION_NAME', 'Test Corp')
        engine.set_variable('CSO_TITLE', 'CISO')

        template = "Welcome to {{ORGANIZATION_NAME}}. Contact the {{CSO_TITLE}}."
        result = engine.substitute(template)

        assert 'Test Corp' in result
        assert 'CISO' in result
        assert '{{' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
