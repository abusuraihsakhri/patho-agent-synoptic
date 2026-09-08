"""
Pytest configuration for Patho Agent Synoptic test suite.
Sets up test environment variables required by security modules.
"""
import os


def pytest_configure(config):
    """Set test environment variables before any tests or imports run."""
    os.environ.setdefault("AUDIT_SECRET_KEY", "test-secret-key-for-pytest-suite-32chars")
