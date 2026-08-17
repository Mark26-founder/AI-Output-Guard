"""Normalizer module for AI Output Guard.

Provides normalization for common AI output formatting variations.
"""

from __future__ import annotations

import re

from ..types import NormalizedOutput, Normalizer, RawOutput


class DefaultNormalizer(Normalizer):
    """Normalizes raw AI text by removing markdown code fences and trimming whitespace."""

    def normalize(self, raw: RawOutput) -> NormalizedOutput:
        content = raw.content
        applied: list[str] = []

        # 1. Strip leading/trailing whitespace
        stripped_content = content.strip()
        if stripped_content != content:
            applied.append("strip_whitespace")
            content = stripped_content

        # 2. Extract content from markdown code fences if present (e.g. ```json ... ``` or ``` ...)
        match = re.match(r"^```(?:[a-zA-Z0-9_-]+)?\s*\n?(.*?)\n?```$", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
            applied.append("strip_markdown_code_fence")

        return NormalizedOutput(content=content, applied_normalizations=tuple(applied))


__all__ = ["DefaultNormalizer"]
