"""Tests for P3 — Schema Validation using Pydantic."""

from pydantic import BaseModel

from ai_output_guard import ParsedOutput, PydanticSchemaValidator


class UserSchema(BaseModel):
    task_id: str
    count: int


class NestedMeta(BaseModel):
    status: str


class ComplexSchema(BaseModel):
    meta: NestedMeta
    items: list[int]


def test_schema_validator_valid_permissive():
    validator = PydanticSchemaValidator(strict=False)
    parsed = ParsedOutput(data={"task_id": "T1", "count": 5}, parser_name="json")
    res = validator.validate(parsed, UserSchema)
    assert res.valid is True
    assert res.data == {"task_id": "T1", "count": 5}
    assert res.errors == ()


def test_schema_validator_missing_field():
    validator = PydanticSchemaValidator()
    parsed = ParsedOutput(data={"task_id": "T1"}, parser_name="json")
    res = validator.validate(parsed, UserSchema)
    assert res.valid is False
    assert len(res.errors) == 1
    assert "count" in res.errors[0].field
    assert "MISSING" in res.errors[0].code


def test_schema_validator_type_mismatch():
    validator = PydanticSchemaValidator()
    parsed = ParsedOutput(data={"task_id": "T1", "count": "not_an_int"}, parser_name="json")
    res = validator.validate(parsed, UserSchema)
    assert res.valid is False
    assert len(res.errors) == 1
    assert "count" in res.errors[0].field


def test_schema_validator_unexpected_field_permissive():
    validator = PydanticSchemaValidator(strict=False)
    raw_data = {"task_id": "T1", "count": 5, "extra": "allowed"}
    parsed = ParsedOutput(data=raw_data, parser_name="json")
    res = validator.validate(parsed, UserSchema)
    assert res.valid is True


def test_schema_validator_unexpected_field_strict():
    validator = PydanticSchemaValidator(strict=True)
    raw_data = {"task_id": "T1", "count": 5, "extra": "not_allowed"}
    parsed = ParsedOutput(data=raw_data, parser_name="json")
    res = validator.validate(parsed, UserSchema)
    assert res.valid is False
    assert len(res.errors) == 1
    assert "extra" in res.errors[0].field
    err_code = res.errors[0].code
    assert "EXTRA" in err_code or "FORBIDDEN" in err_code or "UNEXPECTED" in err_code


def test_schema_validator_nested_structures():
    validator = PydanticSchemaValidator(strict=True)
    parsed = ParsedOutput(
        data={"meta": {"status": "ok"}, "items": [1, 2, 3]}, parser_name="json"
    )
    res = validator.validate(parsed, ComplexSchema)
    assert res.valid is True
    assert res.data == {"meta": {"status": "ok"}, "items": [1, 2, 3]}


def test_schema_validator_nested_field_error():
    validator = PydanticSchemaValidator()
    parsed = ParsedOutput(data={"meta": {"status": 123}, "items": [1, 2]}, parser_name="json")
    res = validator.validate(parsed, ComplexSchema)
    assert res.valid is False
    assert "meta.status" in res.errors[0].field
