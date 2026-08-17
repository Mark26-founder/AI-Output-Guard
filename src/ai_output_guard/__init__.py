"""AI Output Guard

A lightweight validation boundary between AI-generated output
and deterministic application logic.
"""

from .constraint_checker import DefaultConstraintChecker, FieldConstraint
from .guard import Guard
from .normalizer import DefaultNormalizer
from .parser import JSONParser, ParsingError
from .result import GuardResult
from .schema_validator import PydanticSchemaValidator
from .types import (
    ConstraintValidationResult,
    NormalizedOutput,
    ParsedOutput,
    RawOutput,
    SchemaValidationResult,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
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
