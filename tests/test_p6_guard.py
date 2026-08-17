"""Tests for P6 — Guard Pipeline and Public API.

Tests the complete public pipeline: normalization → parsing →
schema validation → constraint validation → GuardResult.
"""

from __future__ import annotations

from pydantic import BaseModel

from ai_output_guard import (
    DefaultConstraintChecker,
    DefaultNormalizer,
    FieldConstraint,
    Guard,
    GuardResult,
    JSONParser,
    PydanticSchemaValidator,
    RawOutput,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


class TaskResult(BaseModel):
    task_id: str
    confidence: float
    status: str
    tags: list[str] = []


class Nested(BaseModel):
    name: str
    metrics: dict[str, float]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_valid_json_returns_success():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "t1", "confidence": 0.9, "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True
    assert result.data is not None
    assert result.data["task_id"] == "t1"
    assert result.errors == ()


def test_result_data_accessible_through_result_data():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "abc", "confidence": 0.5, "status": "DONE"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True
    assert result.data["confidence"] == 0.5


def test_success_produces_guard_result_success_instance():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "x", "confidence": 0.1, "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    assert isinstance(result, GuardResult)
    assert result.ok is True
    assert result.data is not None


# ---------------------------------------------------------------------------
# Normalization → Parsing → Schema flow
# ---------------------------------------------------------------------------


def test_markdown_fence_normalized_then_parsed_successfully():
    guard = Guard()
    raw = RawOutput(content='```json\n{"task_id": "t2", "confidence": 0.7, "status": "RUN"}\n```')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True
    assert result.data["task_id"] == "t2"


def test_whitespace_stripped_before_parsing():
    guard = Guard()
    raw = RawOutput(content='  \n{"task_id": "t3", "confidence": 0.3, "status": "OK"}\n  ')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True


# ---------------------------------------------------------------------------
# Parsing failure
# ---------------------------------------------------------------------------


def test_malformed_json_returns_failure():
    guard = Guard()
    raw = RawOutput(content="{not valid json}")
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "JSON_DECODE_ERROR"
    assert result.data is None


def test_pipeline_stops_after_parsing_failure():
    """Schema and constraint stages must not run when parsing fails."""
    guard = Guard()
    raw = RawOutput(content="not json at all")
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is False
    # Only one parsing error; no schema/constraint errors mixed in
    assert all(e.code == "JSON_DECODE_ERROR" for e in result.errors)


# ---------------------------------------------------------------------------
# Schema validation failure
# ---------------------------------------------------------------------------


def test_missing_required_field_returns_failure():
    guard = Guard()
    # 'task_id' is required
    raw = RawOutput(content='{"confidence": 0.9, "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is False
    assert len(result.errors) >= 1
    assert result.data is None


def test_wrong_type_returns_failure():
    guard = Guard()
    # confidence must be float, not a string
    raw = RawOutput(content='{"task_id": "t4", "confidence": "high", "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is False
    assert result.data is None


def test_pipeline_stops_after_schema_failure():
    """Constraint stage must not run when schema validation fails."""
    guard = Guard()
    raw = RawOutput(content='{"confidence": 0.9, "status": "OK"}')  # missing task_id
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is False
    # Errors are from schema stage only
    assert result.data is None


# ---------------------------------------------------------------------------
# Constraint validation failure
# ---------------------------------------------------------------------------


def test_constraint_violation_returns_failure():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "t5", "confidence": 1.5, "status": "OK"}')
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "MAX_VALUE_VIOLATION"
    assert result.data is None


def test_constraint_allowed_values_violation():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "t6", "confidence": 0.8, "status": "UNKNOWN"}')
    constraints = {"status": FieldConstraint(allowed_values={"OK", "ERROR", "PENDING"})}
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is False
    assert result.errors[0].code == "ALLOWED_VALUES_VIOLATION"


def test_valid_with_constraints_passes():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "t7", "confidence": 0.75, "status": "OK"}')
    constraints = {
        "confidence": FieldConstraint(min_value=0.0, max_value=1.0),
        "status": FieldConstraint(allowed_values={"OK", "ERROR"}),
    }
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is True


def test_constraints_applied_through_p4_implementation():
    """Constraints must use the existing DefaultConstraintChecker (P4)."""
    checker = DefaultConstraintChecker()
    guard = Guard(constraint_checker=checker)
    raw = RawOutput(content='{"task_id": "t8", "confidence": -0.1, "status": "OK"}')
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    result = guard.validate(raw, schema=TaskResult, constraints=constraints)
    assert result.ok is False
    assert result.errors[0].code == "MIN_VALUE_VIOLATION"


# ---------------------------------------------------------------------------
# No constraints — pipeline works without constraint stage
# ---------------------------------------------------------------------------


def test_validate_without_constraints():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "t9", "confidence": 999.0, "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    # No constraints provided → schema passes, constraint stage skipped
    assert result.ok is True


# ---------------------------------------------------------------------------
# Nested / representative data
# ---------------------------------------------------------------------------


def test_nested_schema_valid():
    guard = Guard()
    raw = RawOutput(
        content='{"name": "test", "metrics": {"accuracy": 0.95, "f1": 0.88}}'
    )
    result = guard.validate(raw, schema=Nested)
    assert result.ok is True
    assert result.data["name"] == "test"


def test_nested_schema_invalid_inner_type():
    guard = Guard()
    raw = RawOutput(
        content='{"name": "test", "metrics": {"accuracy": "not_a_float"}}'
    )
    result = guard.validate(raw, schema=Nested)
    assert result.ok is False


# ---------------------------------------------------------------------------
# result.ok accurately reflects outcome
# ---------------------------------------------------------------------------


def test_ok_is_false_on_any_failure():
    guard = Guard()
    cases = [
        RawOutput(content="bad json"),
        RawOutput(content='{"confidence": 0.5}'),  # missing task_id + status
    ]
    for raw in cases:
        result = guard.validate(raw, schema=TaskResult)
        assert result.ok is False, f"Expected ok=False for: {raw.content}"


def test_ok_is_true_only_on_full_success():
    guard = Guard()
    raw = RawOutput(content='{"task_id": "ok", "confidence": 0.5, "status": "DONE"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True
    assert result.data is not None
    assert result.errors == ()


# ---------------------------------------------------------------------------
# Public package import / API usage
# ---------------------------------------------------------------------------


def test_guard_importable_from_package_root():
    """Guard must be importable directly from ai_output_guard."""
    from ai_output_guard import Guard as G  # noqa: PLC0415

    assert G is Guard


def test_guard_raw_output_importable_from_package_root():
    from ai_output_guard import RawOutput as RO  # noqa: PLC0415

    assert RO is RawOutput


def test_full_public_api_usage():
    """End-to-end using only the public package surface."""
    from ai_output_guard import FieldConstraint as FC  # noqa: PLC0415
    from ai_output_guard import Guard as G  # noqa: PLC0415
    from ai_output_guard import RawOutput as RO  # noqa: PLC0415

    guard = G()
    raw = RO(content='{"task_id": "pub", "confidence": 0.6, "status": "OK", "tags": ["a"]}')
    result = guard.validate(
        raw,
        schema=TaskResult,
        constraints={
            "confidence": FC(min_value=0.0, max_value=1.0),
            "tags": FC(min_length=1, max_length=5),
        },
    )
    assert result.ok is True
    assert result.data["task_id"] == "pub"


# ---------------------------------------------------------------------------
# Dependency injection — custom stages can be injected
# ---------------------------------------------------------------------------


def test_guard_accepts_injected_stages():
    guard = Guard(
        normalizer=DefaultNormalizer(),
        parser=JSONParser(),
        schema_validator=PydanticSchemaValidator(),
        constraint_checker=DefaultConstraintChecker(),
    )
    raw = RawOutput(content='{"task_id": "inj", "confidence": 0.4, "status": "OK"}')
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is True


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


def test_errors_accessible_through_result_errors():
    guard = Guard()
    raw = RawOutput(content="{broken}")
    result = guard.validate(raw, schema=TaskResult)
    assert result.ok is False
    assert len(result.errors) > 0
    err = result.errors[0]
    assert err.field is not None
    assert err.code is not None
    assert err.message is not None
