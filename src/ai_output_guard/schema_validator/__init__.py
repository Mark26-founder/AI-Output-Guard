"""Schema Validator module for AI Output Guard.

Provides Pydantic-based schema validation with strict and permissive options.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from ..types import ParsedOutput, SchemaValidationResult, SchemaValidator, ValidationError


class PydanticSchemaValidator(SchemaValidator):
    """Validates parsed data structures against Pydantic models or types."""

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict

    def validate(self, parsed: ParsedOutput, schema: Any) -> SchemaValidationResult:
        data = parsed.data
        errors: list[ValidationError] = []

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            target_model: type[BaseModel] = schema
            if self.strict and getattr(target_model.model_config, "extra", None) != "forbid":
                # Create a dynamically configured model variant that forbids extra fields
                class DynamicStrictModel(target_model):  # type: ignore[misc, valid-type]
                    model_config = ConfigDict(extra="forbid")

                target_model = DynamicStrictModel

            try:
                validated_instance = target_model.model_validate(data)
                return SchemaValidationResult(
                    valid=True, data=validated_instance.model_dump(), errors=()
                )
            except PydanticValidationError as pydantic_err:
                for err in pydantic_err.errors():
                    field_loc = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "$"
                    err_code = err["type"].upper().replace(".", "_")
                    errors.append(
                        ValidationError(
                            field=field_loc,
                            code=err_code,
                            message=err["msg"],
                            expected=err["type"],
                            received=data,
                        )
                    )
                return SchemaValidationResult(valid=False, data=None, errors=tuple(errors))

        # Handle non-BaseModel schemas (e.g. TypeAdapter, lists, dicts, primitive types)
        # using TypeAdapter
        try:
            adapter = schema if isinstance(schema, TypeAdapter) else TypeAdapter(schema)
            validated_data = adapter.validate_python(data, strict=self.strict)
            return SchemaValidationResult(valid=True, data=validated_data, errors=())
        except PydanticValidationError as pydantic_err:
            for err in pydantic_err.errors():
                field_loc = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "$"
                err_code = err["type"].upper().replace(".", "_")
                errors.append(
                    ValidationError(
                        field=field_loc,
                        code=err_code,
                        message=err["msg"],
                        expected=err["type"],
                        received=data,
                    )
                )
            return SchemaValidationResult(valid=False, data=None, errors=tuple(errors))
        except Exception as exc:
            errors.append(
                ValidationError(
                    field="$",
                    code="SCHEMA_ERROR",
                    message=str(exc),
                    expected=str(schema),
                    received=data,
                )
            )
            return SchemaValidationResult(valid=False, data=None, errors=tuple(errors))


__all__ = ["PydanticSchemaValidator"]
