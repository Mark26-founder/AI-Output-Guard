"""Guard pipeline orchestrator for AI Output Guard.

Combines normalization, parsing, schema validation, and constraint validation
into a single deterministic validation flow.
"""

from __future__ import annotations

from typing import Any, TypeVar

from .constraint_checker import DefaultConstraintChecker, FieldConstraint
from .normalizer import DefaultNormalizer
from .parser import JSONParser, ParsingError
from .result import GuardResult
from .schema_validator import PydanticSchemaValidator
from .types import (
    ConstraintChecker,
    Normalizer,
    Parser,
    RawOutput,
    SchemaValidator,
)

T = TypeVar("T")


class Guard:
    """Public API for the AI Output Guard validation pipeline.

    Orchestrates normalization → parsing → schema validation →
    constraint validation and returns a structured GuardResult.

    The application decides what to do after validation; Guard only
    answers whether the output is valid according to the defined contract.

    Usage::

        guard = Guard()
        result = guard.validate(agent_output, schema=TaskResult)

        if result.ok:
            continue_workflow(result.data)
        else:
            handle(result.errors)
    """

    def __init__(
        self,
        *,
        normalizer: Normalizer | None = None,
        parser: Parser | None = None,
        schema_validator: SchemaValidator | None = None,
        constraint_checker: ConstraintChecker | None = None,
    ) -> None:
        self._normalizer: Normalizer = normalizer or DefaultNormalizer()
        self._parser: Parser = parser or JSONParser()
        self._schema_validator: SchemaValidator = schema_validator or PydanticSchemaValidator()
        self._constraint_checker: ConstraintChecker = (
            constraint_checker or DefaultConstraintChecker()
        )

    def validate(
        self,
        raw: RawOutput | str,
        *,
        schema: Any,
        constraints: dict[str, Any] | FieldConstraint | None = None,
    ) -> GuardResult[Any]:
        """Run the full validation pipeline on raw AI output.

        Pipeline stages (in order):
        1. Normalization  — strip whitespace, markdown fences, etc.
        2. Parsing        — decode JSON into a Python data structure.
        3. Schema validation — validate against the given Pydantic schema.
        4. Constraint validation — apply optional value-level constraints.

        The pipeline stops at the first stage that fails; later stages are
        not executed.

        Args:
            raw: Raw AI output to validate.
            schema: Pydantic model or type to validate against.
            constraints: Optional mapping of field names to FieldConstraint
                objects, forwarded directly to the constraint checker.

        Returns:
            GuardResult.success(data) when all stages pass.
            GuardResult.failure(errors) when any stage fails.
        """
        if isinstance(raw, str):
            raw = RawOutput(content=raw)

        # --- Stage 1: Normalization ---
        normalized = self._normalizer.normalize(raw)

        # --- Stage 2: Parsing ---
        try:
            parsed = self._parser.parse(normalized)
        except ParsingError as exc:
            return GuardResult.failure([exc.error])

        # --- Stage 3: Schema Validation ---
        schema_result = self._schema_validator.validate(parsed, schema)
        if not schema_result.valid:
            return GuardResult.failure(list(schema_result.errors))

        # --- Stage 4: Constraint Validation ---
        if constraints is not None:
            constraint_result = self._constraint_checker.check(
                schema_result.data, constraints
            )
            if not constraint_result.valid:
                return GuardResult.failure(list(constraint_result.errors))

        return GuardResult.success(schema_result.data)


__all__ = ["Guard"]
