"""P8 Hardening tests for AI Output Guard.

Comprehensive test suite for edge cases, error conditions, typing, boundary values,
nested validation, custom schemas, and pipeline short-circuit behavior.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, Field, TypeAdapter

from ai_output_guard import (
    DefaultConstraintChecker,
    DefaultNormalizer,
    FieldConstraint,
    Guard,
    JSONParser,
    NormalizedOutput,
    ParsedOutput,
    ParsingError,
    PydanticSchemaValidator,
    RawOutput,
)


class UserProfile(BaseModel):
    name: str
    age: int
    tags: list[str] = Field(default_factory=list)


class Address(BaseModel):
    city: str
    zip_code: str


class PersonWithAddress(BaseModel):
    name: str
    address: Address


# --- 1. Malformed / Unexpected AI Outputs ---

def test_empty_raw_output() -> None:
    guard = Guard()
    result = guard.validate(RawOutput(content=""), schema=UserProfile)
    assert not result.ok
    assert len(result.errors) == 1
    assert result.errors[0].code == "JSON_DECODE_ERROR"


def test_whitespace_only_raw_output() -> None:
    guard = Guard()
    result = guard.validate(RawOutput(content="   \n\t  "), schema=UserProfile)
    assert not result.ok
    assert result.errors[0].code == "JSON_DECODE_ERROR"


def test_truncated_json() -> None:
    guard = Guard()
    result = guard.validate(RawOutput(content='{"name": "Alice", "age":'), schema=UserProfile)
    assert not result.ok
    assert result.errors[0].code == "JSON_DECODE_ERROR"


# --- 2. Normalization Edge Cases ---

def test_normalizer_various_fences() -> None:
    norm = DefaultNormalizer()
    res1 = norm.normalize(RawOutput(content="```python\n{\"name\": \"Bob\", \"age\": 25}\n```"))
    assert res1.content == "{\"name\": \"Bob\", \"age\": 25}"
    assert "strip_markdown_code_fence" in res1.applied_normalizations

    res2 = norm.normalize(RawOutput(content="```json\n{\"a\": 1}\n```\n"))
    assert res2.content == "{\"a\": 1}"

    res3 = norm.normalize(RawOutput(content="plain text without code fence"))
    assert res3.content == "plain text without code fence"
    assert "strip_markdown_code_fence" not in res3.applied_normalizations


# --- 3. JSON Parsing Edge Cases ---

def test_json_parser_primitive_types() -> None:
    parser = JSONParser()
    out1 = parser.parse(NormalizedOutput(content="true"))
    assert out1.data is True

    out2 = parser.parse(NormalizedOutput(content="123.45"))
    assert out2.data == 123.45

    out3 = parser.parse(NormalizedOutput(content="null"))
    assert out3.data is None


def test_json_parser_invalid_syntax_raises_parsing_error() -> None:
    parser = JSONParser()
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(NormalizedOutput(content="{invalid_key: 123}"))
    assert exc_info.value.error.code == "JSON_DECODE_ERROR"


# --- 4. Schema Validation Edge Cases & TypeAdapter ---

def test_schema_validation_non_dict_parsed_data_against_basemodel() -> None:
    validator = PydanticSchemaValidator()
    # Passing a list when a BaseModel is expected
    parsed = ParsedOutput(data=["item1", "item2"], parser_name="json")
    res = validator.validate(parsed, UserProfile)
    assert not res.valid
    assert len(res.errors) > 0
    err_code = res.errors[0].code
    assert "MODEL_TYPE" in err_code or "DICT" in err_code or "TYPE" in err_code


def test_schema_validation_list_schema_via_typeadapter() -> None:
    guard = Guard()
    # Validate raw JSON list against list[int]
    raw = RawOutput(content="[10, 20, 30]")
    result = guard.validate(raw, schema=list[int])
    assert result.ok
    assert result.data == [10, 20, 30]


def test_schema_validation_typeadapter_instance() -> None:
    guard = Guard()
    adapter = TypeAdapter(dict[str, int])
    raw = RawOutput(content='{"a": 1, "b": 2}')
    result = guard.validate(raw, schema=adapter)
    assert result.ok
    assert result.data == {"a": 1, "b": 2}


def test_nested_schema_validation_failure() -> None:
    guard = Guard()
    raw = RawOutput(content='{"name": "Alice", "address": {"city": "NYC"}}')
    result = guard.validate(raw, schema=PersonWithAddress)
    assert not result.ok
    assert any(err.field == "address.zip_code" for err in result.errors)


# --- 5. Constraint Boundary Conditions & Primitive Constraints ---

def test_constraint_exact_numeric_boundaries() -> None:
    checker = DefaultConstraintChecker()
    constraint = FieldConstraint(min_value=0, max_value=100)

    res_min = checker.check(0, constraint)
    assert res_min.valid

    res_max = checker.check(100, constraint)
    assert res_max.valid

    res_below = checker.check(-0.0001, constraint)
    assert not res_below.valid

    res_above = checker.check(100.0001, constraint)
    assert not res_above.valid


def test_constraint_top_level_primitive() -> None:
    guard = Guard()
    constraint = FieldConstraint(min_value=10, max_value=50)
    result_pass = guard.validate("42", schema=int, constraints=constraint)
    assert result_pass.ok
    assert result_pass.data == 42

    result_fail = guard.validate("5", schema=int, constraints=FieldConstraint(min_value=10))
    assert not result_fail.ok
    assert result_fail.errors[0].code == "MIN_VALUE_VIOLATION"


def test_constraint_string_length_boundaries() -> None:
    checker = DefaultConstraintChecker()
    constraint = FieldConstraint(min_length=3, max_length=5)

    data_dict = {"code": "abc"}
    res = checker.check(data_dict, {"code": constraint})
    assert res.valid

    data_too_short = {"code": "ab"}
    res_short = checker.check(data_too_short, {"code": constraint})
    assert not res_short.valid
    assert res_short.errors[0].code == "MIN_LENGTH_VIOLATION"


# --- 6. Multiple Simultaneous Validation Errors ---

def test_multiple_pydantic_validation_errors() -> None:
    guard = Guard()
    # Missing required 'name' and 'age' is wrong type (string instead of int)
    raw = RawOutput(content='{"age": "not_an_int"}')
    result = guard.validate(raw, schema=UserProfile)
    assert not result.ok
    assert len(result.errors) >= 2


def test_multiple_constraint_violations() -> None:
    guard = Guard()
    raw = RawOutput(content='{"name": "A", "age": -5}')
    constraints = {
        "name": FieldConstraint(min_length=3),
        "age": FieldConstraint(min_value=0),
    }
    result = guard.validate(raw, schema=UserProfile, constraints=constraints)
    assert not result.ok
    assert len(result.errors) == 2


# --- 7. Pipeline Short-Circuit Behavior ---

class MockSpyStage:
    def __init__(self) -> None:
        self.called = False

    def check(self, data: Any, constraints: Any) -> Any:
        self.called = True
        return DefaultConstraintChecker().check(data, constraints)


def test_pipeline_short_circuits_on_json_parse_failure() -> None:
    spy_checker = MockSpyStage()
    guard = Guard(constraint_checker=spy_checker)

    c = {"age": FieldConstraint(min_value=0)}
    result = guard.validate("invalid json", schema=UserProfile, constraints=c)
    assert not result.ok
    assert result.errors[0].code == "JSON_DECODE_ERROR"
    assert not spy_checker.called


# --- 8. Direct String Input to Guard ---

def test_guard_validate_accepts_raw_string_directly() -> None:
    guard = Guard()
    result = guard.validate('{"name": "Bob", "age": 30}', schema=UserProfile)
    assert result.ok
    assert result.data == {"name": "Bob", "age": 30, "tags": []}
