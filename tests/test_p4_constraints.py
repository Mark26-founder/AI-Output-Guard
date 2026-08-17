"""Tests for P4 — Constraint Validation."""

from ai_output_guard import DefaultConstraintChecker, FieldConstraint


def test_constraint_checker_valid_numeric_bounds():
    checker = DefaultConstraintChecker()
    data = {"confidence": 0.85, "score": 10}
    constraints = {
        "confidence": FieldConstraint(min_value=0.0, max_value=1.0),
        "score": FieldConstraint(min_value=0, max_value=100),
    }
    res = checker.check(data, constraints)
    assert res.valid is True
    assert res.errors == ()


def test_constraint_checker_exact_boundary_values():
    checker = DefaultConstraintChecker()
    data = {"min_val": 0.0, "max_val": 1.0}
    constraints = {
        "min_val": FieldConstraint(min_value=0.0, max_value=1.0),
        "max_val": FieldConstraint(min_value=0.0, max_value=1.0),
    }
    res = checker.check(data, constraints)
    assert res.valid is True


def test_constraint_checker_below_minimum():
    checker = DefaultConstraintChecker()
    data = {"confidence": -0.1}
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert len(res.errors) == 1
    assert res.errors[0].field == "confidence"
    assert res.errors[0].code == "MIN_VALUE_VIOLATION"


def test_constraint_checker_above_maximum():
    checker = DefaultConstraintChecker()
    data = {"confidence": 1.5}
    constraints = {"confidence": FieldConstraint(min_value=0.0, max_value=1.0)}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert len(res.errors) == 1
    assert res.errors[0].field == "confidence"
    assert res.errors[0].code == "MAX_VALUE_VIOLATION"


def test_constraint_checker_string_length():
    checker = DefaultConstraintChecker()
    data = {"code": "AB"}
    constraints = {"code": FieldConstraint(min_length=3, max_length=5)}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert res.errors[0].code == "MIN_LENGTH_VIOLATION"

    data_long = {"code": "ABCDEF"}
    res_long = checker.check(data_long, constraints)
    assert res_long.valid is False
    assert res_long.errors[0].code == "MAX_LENGTH_VIOLATION"


def test_constraint_checker_collection_length():
    checker = DefaultConstraintChecker()
    data = {"tags": []}
    constraints = {"tags": FieldConstraint(min_length=1, max_length=3)}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert res.errors[0].code == "MIN_COLLECTION_LENGTH_VIOLATION"

    data_too_many = {"tags": ["a", "b", "c", "d"]}
    res_too_many = checker.check(data_too_many, constraints)
    assert res_too_many.valid is False
    assert res_too_many.errors[0].code == "MAX_COLLECTION_LENGTH_VIOLATION"


def test_constraint_checker_allowed_values():
    checker = DefaultConstraintChecker()
    data = {"status": "INVALID_STATUS"}
    constraints = {"status": FieldConstraint(allowed_values={"PENDING", "APPROVED", "REJECTED"})}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert res.errors[0].code == "ALLOWED_VALUES_VIOLATION"


def test_constraint_checker_nested_fields():
    checker = DefaultConstraintChecker()
    data = {"metrics": {"score": 150}}
    constraints = {"metrics": {"score": FieldConstraint(max_value=100)}}
    res = checker.check(data, constraints)
    assert res.valid is False
    assert res.errors[0].field == "metrics.score"
    assert res.errors[0].code == "MAX_VALUE_VIOLATION"


def test_constraint_checker_multiple_violations():
    checker = DefaultConstraintChecker()
    data = {"confidence": 2.0, "status": "UNKNOWN"}
    constraints = {
        "confidence": FieldConstraint(min_value=0.0, max_value=1.0),
        "status": FieldConstraint(allowed_values={"OK", "ERROR"}),
    }
    res = checker.check(data, constraints)
    assert res.valid is False
    assert len(res.errors) == 2
