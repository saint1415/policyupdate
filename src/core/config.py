"""
Configuration Module
Centralized configuration management for the GRC Policy Management Platform
"""

import os
import logging
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DatabaseConfig:
    """Database configuration"""
    clients_db: str = "clients.db"
    feeds_db: str = "feeds.db"


@dataclass
class WebConfig:
    """Web server configuration"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = field(default_factory=lambda: os.environ.get(
        'POLICYUPDATE_SECRET_KEY',
        secrets.token_hex(32)
    ))


@dataclass
class NotificationConfig:
    """Notification settings"""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    webhook_url: str = ""


@dataclass
class AppConfig:
    """Main application configuration"""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    policies_dir: str = "policies"
    frameworks_dir: str = "config/frameworks"
    output_dir: str = "output"
    data_dir: str = "data"

    # Sub-configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    web: WebConfig = field(default_factory=WebConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)

    # Logging
    log_level: str = field(default_factory=lambda: os.environ.get('POLICYUPDATE_LOG_LEVEL', 'INFO'))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None

    def get_policies_path(self) -> Path:
        """Get absolute path to policies directory"""
        return self.project_root / self.policies_dir

    def get_frameworks_path(self) -> Path:
        """Get absolute path to frameworks directory"""
        return self.project_root / self.frameworks_dir

    def get_output_path(self) -> Path:
        """Get absolute path to output directory"""
        path = self.project_root / self.output_dir
        path.mkdir(exist_ok=True)
        return path

    def get_data_path(self) -> Path:
        """Get absolute path to data directory"""
        path = self.project_root / self.data_dir
        path.mkdir(exist_ok=True)
        return path


def setup_logging(config: Optional[AppConfig] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        config: Optional AppConfig. If not provided, uses defaults.

    Returns:
        Root logger for the policyupdate application
    """
    if config is None:
        config = AppConfig()

    # Get numeric log level
    numeric_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(config.log_format)

    # Get or create the policyupdate logger
    logger = logging.getLogger('policyupdate')
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (e.g., 'core.compliance_mapper')

    Returns:
        Logger instance
    """
    return logging.getLogger(f'policyupdate.{name}')


# Global default config (can be overridden)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the current application configuration"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def set_config(config: AppConfig) -> None:
    """Set the application configuration"""
    global _config
    _config = config


def load_config_from_env() -> AppConfig:
    """
    Load configuration from environment variables.

    Environment variables:
        POLICYUPDATE_SECRET_KEY: Flask secret key
        POLICYUPDATE_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        POLICYUPDATE_LOG_FILE: Path to log file
        POLICYUPDATE_SMTP_HOST: SMTP server host
        POLICYUPDATE_SMTP_PORT: SMTP server port
        POLICYUPDATE_SMTP_USER: SMTP username
        POLICYUPDATE_SMTP_PASSWORD: SMTP password
        POLICYUPDATE_EMAIL_FROM: From email address
        POLICYUPDATE_WEBHOOK_URL: Webhook URL for notifications
    """
    config = AppConfig()

    # Web config
    if os.environ.get('POLICYUPDATE_SECRET_KEY'):
        config.web.secret_key = os.environ['POLICYUPDATE_SECRET_KEY']
    if os.environ.get('POLICYUPDATE_DEBUG'):
        config.web.debug = os.environ['POLICYUPDATE_DEBUG'].lower() == 'true'

    # Logging config
    if os.environ.get('POLICYUPDATE_LOG_LEVEL'):
        config.log_level = os.environ['POLICYUPDATE_LOG_LEVEL']
    if os.environ.get('POLICYUPDATE_LOG_FILE'):
        config.log_file = os.environ['POLICYUPDATE_LOG_FILE']

    # Notification config
    if os.environ.get('POLICYUPDATE_SMTP_HOST'):
        config.notification.smtp_host = os.environ['POLICYUPDATE_SMTP_HOST']
    if os.environ.get('POLICYUPDATE_SMTP_PORT'):
        config.notification.smtp_port = int(os.environ['POLICYUPDATE_SMTP_PORT'])
    if os.environ.get('POLICYUPDATE_SMTP_USER'):
        config.notification.smtp_user = os.environ['POLICYUPDATE_SMTP_USER']
    if os.environ.get('POLICYUPDATE_SMTP_PASSWORD'):
        config.notification.smtp_password = os.environ['POLICYUPDATE_SMTP_PASSWORD']
    if os.environ.get('POLICYUPDATE_EMAIL_FROM'):
        config.notification.email_from = os.environ['POLICYUPDATE_EMAIL_FROM']
    if os.environ.get('POLICYUPDATE_WEBHOOK_URL'):
        config.notification.webhook_url = os.environ['POLICYUPDATE_WEBHOOK_URL']

    return config
