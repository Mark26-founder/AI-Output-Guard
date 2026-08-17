"""Shared type definitions for AI Output Guard pipeline stages.

These types define the data structures that flow through the validation pipeline
without implementing any pipeline logic. They are intentionally minimal and
concrete, serving as stable interfaces between stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RawOutput:
    """Raw AI output as received from the source.

    This is the entry point of the pipeline - unprocessed, untrusted input.
    """

    content: str
    source: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class NormalizedOutput:
    """Output after normalization stage.

    Normalization handles representation-level noise (e.g., formatting wrappers)
    without altering semantic meaning of valid data.
    """

    content: str
    applied_normalizations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParsedOutput:
    """Output after parsing stage.

    Parsed into a structured representation suitable for validation.
    """

    data: Any
    parser_name: str


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single validation error with field-level detail."""

    field: str
    code: str
    message: str
    expected: Any | None = None
    received: Any | None = None


@dataclass(frozen=True, slots=True)
class SchemaValidationResult:
    """Result of schema validation stage."""

    valid: bool
    data: Any | None = None
    errors: tuple[ValidationError, ...] = ()


@dataclass(frozen=True, slots=True)
class ConstraintValidationResult:
    """Result of constraint validation stage."""

    valid: bool
    data: Any | None = None
    errors: tuple[ValidationError, ...] = ()


class Parser(Protocol):
    """Protocol for output parsers."""

    def parse(self, normalized: NormalizedOutput) -> ParsedOutput:
        """Parse normalized output."""
        ...


class Normalizer(Protocol):
    """Protocol for output normalizers."""

    def normalize(self, raw: RawOutput) -> NormalizedOutput:
        """Normalize raw AI output."""
        ...


class SchemaValidator(Protocol):
    """Protocol for schema validators."""

    def validate(self, parsed: ParsedOutput, schema: Any) -> SchemaValidationResult:
        """Validate parsed output against schema."""
        ...


class ConstraintChecker(Protocol):
    """Protocol for constraint checkers."""

    def check(self, data: Any, constraints: Any) -> ConstraintValidationResult:
        """Check constraints against validated data."""
        ...
