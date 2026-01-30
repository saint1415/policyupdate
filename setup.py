#!/usr/bin/env python3
"""
PolicyUpdate - GRC Policy Management Platform
Setup script for package installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="policyupdate",
    version="1.0.0",
    author="saint1415",
    description="GRC Policy Management Platform for compliance-mapped policy generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/saint1415/policyupdate",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyYAML>=6.0",
        "click>=8.1",
    ],
    extras_require={
        "docx": ["python-docx>=0.8.11"],
        "pdf": ["weasyprint>=60.0"],
        "web": ["flask>=3.0", "flask-cors>=4.0"],
        "monitor": ["feedparser>=6.0", "requests>=2.31", "beautifulsoup4>=4.12"],
        "all": [
            "python-docx>=0.8.11",
            "weasyprint>=60.0",
            "flask>=3.0",
            "flask-cors>=4.0",
            "feedparser>=6.0",
            "requests>=2.31",
            "beautifulsoup4>=4.12",
        ],
        "dev": [
            "pytest>=7.4",
            "pytest-cov>=4.1",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "policy-grc=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.md"],
    },
    data_files=[
        ("config/frameworks", [
            "config/frameworks/nist_csf_2.0.yaml",
            "config/frameworks/iso_27001_2022.yaml",
            "config/frameworks/soc2.yaml",
            "config/frameworks/pci_dss_4.yaml",
            "config/frameworks/hipaa.yaml",
            "config/frameworks/gdpr.yaml",
            "config/frameworks/ccpa.yaml",
            "config/frameworks/sec_cyber.yaml",
            "config/frameworks/nist_800_171.yaml",
            "config/frameworks/nis2.yaml",
            "config/frameworks/eu_ai_act.yaml",
        ]),
    ],
)
