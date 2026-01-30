"""
Generation Module Tests
Tests for package building and export functionality
"""

import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest


class TestPackageBuilder:
    """Tests for the PackageBuilder class"""

    @pytest.fixture
    def builder(self):
        from generation.package_builder import PackageBuilder
        return PackageBuilder(
            str(PROJECT_ROOT / "policies"),
            str(PROJECT_ROOT / "config" / "frameworks")
        )

    def test_load_policies(self, builder):
        """Test that builder loads all policies"""
        policies = builder.get_all_policies()
        assert len(policies) >= 186

    def test_build_package_soc2(self, builder):
        """Test building a SOC 2 package"""
        from generation.package_builder import ClientConfig

        config = ClientConfig(
            name="Test Company",
            variables={"ORGANIZATION_NAME": "Test Company"},
            frameworks=["soc2"]
        )

        result = builder.build_package(config)
        assert result.total_policies > 0
        assert result.client_name == "Test Company"
        assert "soc2" in result.frameworks_covered

    def test_build_package_multiple_frameworks(self, builder):
        """Test building with multiple frameworks"""
        from generation.package_builder import ClientConfig

        config = ClientConfig(
            name="Multi-Framework Corp",
            variables={"ORGANIZATION_NAME": "Multi-Framework Corp"},
            frameworks=["soc2", "hipaa", "gdpr"]
        )

        result = builder.build_package(config)
        assert result.total_policies > 60  # Should include policies from all frameworks

    def test_variable_substitution(self, builder):
        """Test that variables are substituted in output"""
        from generation.package_builder import ClientConfig

        config = ClientConfig(
            name="Acme Corp",
            variables={
                "ORGANIZATION_NAME": "Acme Corporation",
                "CSO_TITLE": "Chief Information Security Officer"
            },
            frameworks=["soc2"]
        )

        result = builder.build_package(config)

        # Check at least one policy has substituted content
        substituted = False
        for policy in result.policies:
            if "Acme Corporation" in policy.content:
                substituted = True
                break

        assert substituted, "Variables should be substituted in policy content"

    def test_generate_toc(self, builder):
        """Test table of contents generation"""
        from generation.package_builder import ClientConfig

        config = ClientConfig(
            name="TOC Test",
            variables={"ORGANIZATION_NAME": "TOC Test"},
            frameworks=["soc2"]
        )

        result = builder.build_package(config)
        toc = builder.generate_table_of_contents(result)

        assert "Table of Contents" in toc
        assert "TOC Test" in toc

    def test_generate_checklist(self, builder):
        """Test customization checklist generation"""
        from generation.package_builder import ClientConfig

        config = ClientConfig(
            name="Checklist Test",
            variables={"ORGANIZATION_NAME": "Checklist Test"},
            frameworks=["soc2"]
        )

        result = builder.build_package(config)
        checklist = builder.generate_customization_checklist(result)

        assert "Customization Checklist" in checklist


class TestDocxExporter:
    """Tests for DOCX export"""

    @pytest.fixture
    def package_result(self):
        from generation.package_builder import PackageBuilder, ClientConfig

        builder = PackageBuilder(
            str(PROJECT_ROOT / "policies"),
            str(PROJECT_ROOT / "config" / "frameworks")
        )

        config = ClientConfig(
            name="Export Test",
            variables={"ORGANIZATION_NAME": "Export Test Inc"},
            frameworks=["soc2"]
        )

        return builder.build_package(config)

    def test_docx_export(self, package_result, tmp_path):
        """Test DOCX export creates file"""
        try:
            from generation.docx_exporter import DocxExporter
        except ImportError:
            pytest.skip("python-docx not installed")

        exporter = DocxExporter()
        output_path = tmp_path / "test_output.docx"
        exporter.export_package(package_result, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # Should be non-trivial size


class TestPdfExporter:
    """Tests for PDF export"""

    @pytest.fixture
    def package_result(self):
        from generation.package_builder import PackageBuilder, ClientConfig

        builder = PackageBuilder(
            str(PROJECT_ROOT / "policies"),
            str(PROJECT_ROOT / "config" / "frameworks")
        )

        config = ClientConfig(
            name="PDF Test",
            variables={"ORGANIZATION_NAME": "PDF Test Inc"},
            frameworks=["soc2"]
        )

        return builder.build_package(config)

    def test_pdf_export(self, package_result, tmp_path):
        """Test PDF export creates file"""
        try:
            from generation.pdf_exporter import PdfExporter
        except ImportError:
            pytest.skip("weasyprint not installed")

        exporter = PdfExporter()
        output_path = tmp_path / "test_output.pdf"
        exporter.export_package(package_result, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
