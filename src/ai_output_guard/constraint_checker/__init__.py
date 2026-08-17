"""Constraint Checker module for AI Output Guard.

Provides deterministic value-level constraint validation on validated data structures.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from ..types import ConstraintChecker, ConstraintValidationResult, ValidationError


@dataclass(frozen=True, slots=True)
class FieldConstraint:
    """Defines value-level constraints for a field."""

    min_value: float | int | None = None
    max_value: float | int | None = None
    min_length: int | None = None
    max_length: int | None = None
    allowed_values: Collection[Any] | None = None


class DefaultConstraintChecker(ConstraintChecker):
    """Validates deterministic value-level constraints against data objects/dictionaries."""

    def check(self, data: Any, constraints: Any) -> ConstraintValidationResult:
        errors: list[ValidationError] = []

        if isinstance(constraints, FieldConstraint):
            self._check_value(data, constraints, "$", errors)
            return ConstraintValidationResult(
                valid=len(errors) == 0, data=data, errors=tuple(errors)
            )

        if not isinstance(constraints, dict):
            return ConstraintValidationResult(valid=True, data=data, errors=())

        if isinstance(data, dict):
            self._check_dict(data, constraints, "$", errors)
        else:
            # Single object attribute access if constraints is a dict of attr -> FieldConstraint
            for field_name, constraint in constraints.items():
                if hasattr(data, field_name):
                    val = getattr(data, field_name)
                    self._check_value(val, constraint, field_name, errors)

        return ConstraintValidationResult(
            valid=len(errors) == 0, data=data, errors=tuple(errors)
        )

    def _check_dict(
        self,
        data: dict[str, Any],
        constraints: dict[str, Any],
        path: str,
        errors: list[ValidationError],
    ) -> None:
        for field, constraint in constraints.items():
            field_path = f"{path}.{field}" if path != "$" else field

            if isinstance(constraint, dict) and not isinstance(constraint, FieldConstraint):
                # Nested constraint dictionary
                if field in data and isinstance(data[field], dict):
                    self._check_dict(data[field], constraint, field_path, errors)
            elif field in data and data[field] is not None:
                self._check_value(data[field], constraint, field_path, errors)

    def _check_value(
        self, value: Any, constraint: Any, field_path: str, errors: list[ValidationError]
    ) -> None:
        if not isinstance(constraint, FieldConstraint):
            return

        # Numeric Min / Max
        if isinstance(value, (int, float)):
            if constraint.min_value is not None and value < constraint.min_value:
                errors.append(
                    ValidationError(
                        field=field_path,
                        code="MIN_VALUE_VIOLATION",
                        message=f"Value {value} is below minimum {constraint.min_value}",
                        expected=f">= {constraint.min_value}",
                        received=value,
                    )
                )
            if constraint.max_value is not None and value > constraint.max_value:
                errors.append(
                    ValidationError(
                        field=field_path,
                        code="MAX_VALUE_VIOLATION",
                        message=f"Value {value} is above maximum {constraint.max_value}",
                        expected=f"<= {constraint.max_value}",
                        received=value,
                    )
                )

        # String or Collection Min / Max length
        if isinstance(value, (str, list, tuple, set, dict)):
            val_len = len(value)
            is_str = isinstance(value, str)
            code_prefix = "MIN_LENGTH" if is_str else "MIN_COLLECTION_LENGTH"
            if constraint.min_length is not None and val_len < constraint.min_length:
                errors.append(
                    ValidationError(
                        field=field_path,
                        code=f"{code_prefix}_VIOLATION",
                        message=f"Length {val_len} is below minimum length {constraint.min_length}",
                        expected=f"length >= {constraint.min_length}",
                        received=val_len,
                    )
                )
            code_prefix = "MAX_LENGTH" if is_str else "MAX_COLLECTION_LENGTH"
            if constraint.max_length is not None and val_len > constraint.max_length:
                errors.append(
                    ValidationError(
                        field=field_path,
                        code=f"{code_prefix}_VIOLATION",
                        message=f"Length {val_len} exceeds maximum length {constraint.max_length}",
                        expected=f"length <= {constraint.max_length}",
                        received=val_len,
                    )
                )

        # Allowed values / Membership
        if constraint.allowed_values is not None:
            if value not in constraint.allowed_values:
                allowed_str = str(constraint.allowed_values)
                errors.append(
                    ValidationError(
                        field=field_path,
                        code="ALLOWED_VALUES_VIOLATION",
                        message=f"Value '{value}' is not in allowed values: {allowed_str}",
                        expected=constraint.allowed_values,
                        received=value,
                    )
                )


__all__ = ["FieldConstraint", "DefaultConstraintChecker"]
