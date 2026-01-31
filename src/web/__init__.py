"""
Web Interface Module
Flask-based web interface for the GRC platform
"""


def create_app(config=None):
    """Lazy import to avoid circular dependencies"""
    from .app import create_app as _create_app
    return _create_app(config)


__all__ = ['create_app']
