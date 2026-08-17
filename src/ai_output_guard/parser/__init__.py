"""Parser module for AI Output Guard.

Provides JSON parsing and structured parsing failure handling.
"""

from __future__ import annotations

import json

from ..types import NormalizedOutput, ParsedOutput, Parser, ValidationError


class ParsingError(Exception):
    """Exception raised when parsing structured output fails."""

    def __init__(self, error: ValidationError) -> None:
        self.error = error
        super().__init__(error.message)


class JSONParser(Parser):
    """Parses normalized JSON strings into Python data structures."""

    def parse(self, normalized: NormalizedOutput) -> ParsedOutput:
        try:
            data = json.loads(normalized.content)
            return ParsedOutput(data=data, parser_name="json")
        except json.JSONDecodeError as err:
            validation_err = ValidationError(
                field="$",
                code="JSON_DECODE_ERROR",
                message=f"Failed to parse JSON output: {err.msg}",
                expected="Valid JSON string",
                received=normalized.content,
            )
            raise ParsingError(validation_err) from err


__all__ = ["JSONParser", "ParsingError"]
