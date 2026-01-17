"""Pytest configuration for integration tests."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires external resources)",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (may take significant time to run)",
    )
