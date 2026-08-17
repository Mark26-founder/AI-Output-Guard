"""Result module for AI Output Guard.

Provides the unified GuardResult success/failure model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ..types import ValidationError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class GuardResult(Generic[T]):
    """Unified validation result object returned by the Guard pipeline."""

    ok: bool
    data: T | None = None
    errors: tuple[ValidationError, ...] = ()

    @classmethod
    def success(cls, data: T) -> GuardResult[T]:
        """Create a successful GuardResult."""
        return cls(ok=True, data=data, errors=())

    @classmethod
    def failure(cls, errors: tuple[ValidationError, ...] | list[ValidationError]) -> GuardResult[T]:
        """Create a failed GuardResult with structured errors."""
        return cls(ok=False, data=None, errors=tuple(errors))


__all__ = ["GuardResult"]
