"""Integration and end-to-end public usage tests for AI Output Guard (P7)."""

from __future__ import annotations

from pydantic import BaseModel

import ai_output_guard
from ai_output_guard import (
    FieldConstraint,
    Guard,
    RawOutput,
)


class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    tags: list[str] = []


def test_public_package_exports():
    """Verify that all public components are exported cleanly from package root."""
    expected_exports = [
        "Guard",
        "RawOutput",
        "NormalizedOutput",
        "ParsedOutput",
        "ValidationError",
        "SchemaValidationResult",
        "ConstraintValidationResult",
        "GuardResult",
        "DefaultNormalizer",
        "JSONParser",
        "ParsingError",
        "PydanticSchemaValidator",
        "FieldConstraint",
        "DefaultConstraintChecker",
    ]
    for export_name in expected_exports:
        assert hasattr(ai_output_guard, export_name)
        assert export_name in ai_output_guard.__all__


def test_py_typed_marker_present():
    """Verify py.typed marker is present in package data for PEP 561 compliance."""
    import pathlib

    package_dir = pathlib.Path(ai_output_guard.__file__).parent
    py_typed_file = package_dir / "py.typed"
    assert py_typed_file.exists()
    assert py_typed_file.is_file()


def test_end_to_end_integration_flow():
    """Simulate a realistic public integration flow with Guard."""
    guard = Guard()
    raw_ai_response = RawOutput(
        content='''
        ```json
        {
            "user_id": 42,
            "username": "admin_user",
            "email": "admin@example.com",
            "role": "ADMIN",
            "tags": ["super", "active"]
        }
        ```
        '''
    )
    constraints = {
        "role": FieldConstraint(allowed_values={"ADMIN", "USER", "GUEST"}),
        "tags": FieldConstraint(min_length=1, max_length=5),
    }

    result = guard.validate(raw_ai_response, schema=UserProfile, constraints=constraints)

    assert result.ok is True
    assert result.data is not None
    assert result.data["user_id"] == 42
    assert result.data["role"] == "ADMIN"
    assert len(result.errors) == 0


def test_integration_flow_with_constraint_rejection():
    """Simulate public integration flow where value constraint fails."""
    guard = Guard()
    raw_ai_response = RawOutput(
        content='{"user_id": 42, "username": "usr", "email": "a@b.com", "role": "SUPERUSER"}'
    )
    constraints = {
        "role": FieldConstraint(allowed_values={"ADMIN", "USER", "GUEST"}),
    }

    result = guard.validate(raw_ai_response, schema=UserProfile, constraints=constraints)

    assert result.ok is False
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].code == "ALLOWED_VALUES_VIOLATION"
