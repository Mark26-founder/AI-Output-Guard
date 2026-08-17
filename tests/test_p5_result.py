"""Tests for P5 — Result and Error System."""

from ai_output_guard import (
    ConstraintValidationResult,
    GuardResult,
    ParsingError,
    SchemaValidationResult,
    ValidationError,
)


def test_guard_result_success():
    data = {"task_id": "T-100", "score": 98.5}
    res = GuardResult.success(data)
    assert res.ok is True
    assert res.data == data
    assert res.errors == ()


def test_guard_result_failure():
    err1 = ValidationError(
        field="score", code="MAX_VALUE", message="Too high", expected=100, received=150
    )
    err2 = ValidationError(
        field="task_id", code="MISSING", message="Required", expected="str", received=None
    )
    res = GuardResult.failure((err1, err2))
    assert res.ok is False
    assert res.data is None
    assert len(res.errors) == 2
    assert res.errors[0].field == "score"
    assert res.errors[1].field == "task_id"


def test_guard_result_from_parsing_error():
    err = ValidationError(field="$", code="JSON_DECODE_ERROR", message="Invalid JSON")
    pe = ParsingError(err)
    res = GuardResult.failure((pe.error,))
    assert res.ok is False
    assert res.errors[0].code == "JSON_DECODE_ERROR"


def test_guard_result_from_schema_validation():
    err = ValidationError(field="age", code="TYPE_MISMATCH", message="Expected int")
    svr = SchemaValidationResult(valid=False, errors=(err,))
    res = GuardResult.failure(svr.errors)
    assert res.ok is False
    assert res.errors[0].field == "age"


def test_guard_result_from_constraint_validation():
    err = ValidationError(field="confidence", code="MIN_VALUE", message="Must be >= 0")
    cvr = ConstraintValidationResult(valid=False, errors=(err,))
    res = GuardResult.failure(cvr.errors)
    assert res.ok is False
    assert res.errors[0].field == "confidence"


def test_guard_result_immutability():
    res = GuardResult.success({"key": "val"})
    try:
        res.ok = False  # type: ignore[misc]
        raise AssertionError("Expected frozen error")
    except Exception as exc:
        assert "frozen" in str(exc).lower() or "cannot assign" in str(exc).lower()
