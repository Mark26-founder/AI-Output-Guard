"""Tests for P1 — Package Foundation: core type definitions."""

from ai_output_guard.types import (
    ConstraintValidationResult,
    NormalizedOutput,
    ParsedOutput,
    RawOutput,
    SchemaValidationResult,
    ValidationError,
)


def test_raw_output_minimal():
    """RawOutput accepts content-only construction."""
    r = RawOutput(content="hello")
    assert r.content == "hello"
    assert r.source is None
    assert r.metadata is None


def test_raw_output_full():
    """RawOutput stores all fields correctly."""
    r = RawOutput(content="data", source="gpt-4", metadata={"tokens": 10})
    assert r.source == "gpt-4"
    assert r.metadata == {"tokens": 10}


def test_raw_output_is_frozen():
    """RawOutput is immutable."""
    r = RawOutput(content="x")
    try:
        r.content = "y"  # type: ignore[misc]
        raise AssertionError("Expected FrozenInstanceError")
    except Exception as exc:
        assert "frozen" in str(exc).lower() or "cannot assign" in str(exc).lower()


def test_normalized_output_defaults():
    """NormalizedOutput defaults to empty normalizations tuple."""
    n = NormalizedOutput(content="clean")
    assert n.content == "clean"
    assert n.applied_normalizations == ()


def test_normalized_output_with_normalizations():
    """NormalizedOutput stores applied normalization names."""
    n = NormalizedOutput(content="clean", applied_normalizations=("strip_markdown",))
    assert "strip_markdown" in n.applied_normalizations


def test_parsed_output():
    """ParsedOutput stores structured data and parser name."""
    p = ParsedOutput(data={"key": "value"}, parser_name="json")
    assert p.data == {"key": "value"}
    assert p.parser_name == "json"


def test_validation_error_minimal():
    """ValidationError stores required fields."""
    e = ValidationError(field="confidence", code="TYPE_ERROR", message="Expected float")
    assert e.field == "confidence"
    assert e.code == "TYPE_ERROR"
    assert e.expected is None
    assert e.received is None


def test_validation_error_full():
    """ValidationError stores optional expected/received."""
    e = ValidationError(
        field="score",
        code="RANGE_ERROR",
        message="Out of range",
        expected="0.0–1.0",
        received=2.5,
    )
    assert e.expected == "0.0–1.0"
    assert e.received == 2.5


def test_schema_validation_result_success():
    """SchemaValidationResult reflects a passing result."""
    r = SchemaValidationResult(valid=True, data={"x": 1})
    assert r.valid is True
    assert r.data == {"x": 1}
    assert r.errors == ()


def test_schema_validation_result_failure():
    """SchemaValidationResult reflects a failing result with errors."""
    err = ValidationError(field="name", code="MISSING", message="Required field missing")
    r = SchemaValidationResult(valid=False, errors=(err,))
    assert r.valid is False
    assert len(r.errors) == 1
    assert r.errors[0].code == "MISSING"


def test_constraint_validation_result_success():
    """ConstraintValidationResult reflects a passing constraint check."""
    r = ConstraintValidationResult(valid=True, data={"confidence": 0.9})
    assert r.valid is True
    assert r.errors == ()


def test_constraint_validation_result_failure():
    """ConstraintValidationResult reflects constraint failures."""
    err = ValidationError(
        field="confidence", code="CONSTRAINT_VIOLATION", message="Must be <= 1.0"
    )
    r = ConstraintValidationResult(valid=False, errors=(err,))
    assert r.valid is False
    assert r.errors[0].field == "confidence"


def test_submodule_imports():
    """All pipeline submodule packages are importable."""
    import ai_output_guard.constraint_checker
    import ai_output_guard.normalizer
    import ai_output_guard.parser
    import ai_output_guard.result
    import ai_output_guard.schema_validator

    # Each should expose __all__ (even if empty at this stage)
    assert hasattr(ai_output_guard.normalizer, "__all__")
    assert hasattr(ai_output_guard.parser, "__all__")
    assert hasattr(ai_output_guard.schema_validator, "__all__")
    assert hasattr(ai_output_guard.constraint_checker, "__all__")
    assert hasattr(ai_output_guard.result, "__all__")


def test_top_level_exports():
    """Top-level package exports all P1 types."""
    import ai_output_guard as aog

    for name in [
        "RawOutput",
        "NormalizedOutput",
        "ParsedOutput",
        "ValidationError",
        "SchemaValidationResult",
        "ConstraintValidationResult",
    ]:
        assert hasattr(aog, name), f"Missing export: {name}"
