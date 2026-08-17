"""Pytest configuration for AI Output Guard."""

import pytest


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure clean state for each test."""
    yield
    # Teardown if needed
