"""Basic package tests to verify test infrastructure."""

import ai_output_guard


def test_package_imports():
    """Verify the package can be imported."""
    assert ai_output_guard.__version__ == "0.1.0"


def test_package_has_version():
    """Verify version is exposed."""
    assert hasattr(ai_output_guard, "__version__")
    assert isinstance(ai_output_guard.__version__, str)
