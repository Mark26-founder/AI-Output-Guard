"""Tests for P2 — Parsing and Normalization."""

import pytest

from ai_output_guard import (
    DefaultNormalizer,
    JSONParser,
    NormalizedOutput,
    ParsedOutput,
    ParsingError,
    RawOutput,
)


# Normalizer Tests
def test_normalizer_plain_text():
    normalizer = DefaultNormalizer()
    raw = RawOutput(content='{"name": "test"}')
    normalized = normalizer.normalize(raw)
    assert normalized.content == '{"name": "test"}'
    assert normalized.applied_normalizations == ()


def test_normalizer_strip_whitespace():
    normalizer = DefaultNormalizer()
    raw = RawOutput(content='  \n{"name": "test"}\n  ')
    normalized = normalizer.normalize(raw)
    assert normalized.content == '{"name": "test"}'
    assert "strip_whitespace" in normalized.applied_normalizations


def test_normalizer_strip_markdown_code_fence_with_language():
    normalizer = DefaultNormalizer()
    raw = RawOutput(content='```json\n{"name": "test"}\n```')
    normalized = normalizer.normalize(raw)
    assert normalized.content == '{"name": "test"}'
    assert "strip_markdown_code_fence" in normalized.applied_normalizations


def test_normalizer_strip_markdown_code_fence_without_language():
    normalizer = DefaultNormalizer()
    raw = RawOutput(content='```\n{"name": "test"}\n```')
    normalized = normalizer.normalize(raw)
    assert normalized.content == '{"name": "test"}'
    assert "strip_markdown_code_fence" in normalized.applied_normalizations


def test_normalizer_combined_whitespace_and_markdown():
    normalizer = DefaultNormalizer()
    raw = RawOutput(content='  \n```json\n{"name": "test"}\n```\n  ')
    normalized = normalizer.normalize(raw)
    assert normalized.content == '{"name": "test"}'
    assert "strip_whitespace" in normalized.applied_normalizations
    assert "strip_markdown_code_fence" in normalized.applied_normalizations


# JSONParser Tests
def test_json_parser_valid_object():
    parser = JSONParser()
    normalized = NormalizedOutput(content='{"key": "value", "num": 123}')
    parsed = parser.parse(normalized)
    assert isinstance(parsed, ParsedOutput)
    assert parsed.parser_name == "json"
    assert parsed.data == {"key": "value", "num": 123}


def test_json_parser_valid_list():
    parser = JSONParser()
    normalized = NormalizedOutput(content='[1, 2, 3]')
    parsed = parser.parse(normalized)
    assert parsed.data == [1, 2, 3]


def test_json_parser_malformed_json():
    parser = JSONParser()
    normalized = NormalizedOutput(content='{"key": "value"')
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(normalized)

    err = exc_info.value.error
    assert err.field == "$"
    assert err.code == "JSON_DECODE_ERROR"
    assert err.received == '{"key": "value"'


def test_json_parser_empty_string():
    parser = JSONParser()
    normalized = NormalizedOutput(content='')
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(normalized)
    assert exc_info.value.error.code == "JSON_DECODE_ERROR"
