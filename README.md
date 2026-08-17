# AI Output Guard

> A lightweight validation boundary between AI-generated output and deterministic application logic.

## Purpose

AI systems are probabilistic, while the software consuming their outputs is usually deterministic. An AI model may return malformed JSON, missing fields, incorrect data types, invalid values, or outputs that violate application-level constraints.

AI Output Guard provides a validation layer that catches these failures before they reach your application logic.

## Installation

```bash
pip install ai-output-guard
```

## Quick Start

```python
from ai_output_guard import FieldConstraint, Guard, RawOutput
from pydantic import BaseModel

class TaskResult(BaseModel):
    task_id: str
    confidence: float
    tags: list[str]

guard = Guard()

raw = RawOutput(content='''
```json
{
    "task_id": "task-123",
    "confidence": 0.95,
    "tags": ["processing", "urgent"]
}
```
''')

constraints = {
    "confidence": FieldConstraint(min_value=0.0, max_value=1.0),
    "tags": FieldConstraint(min_length=1, max_length=5),
}

result = guard.validate(raw, schema=TaskResult, constraints=constraints)

if result.ok:
    print("Validated Data:", result.data)
else:
    print("Validation Errors:", result.errors)
```

## Core Features & Pipeline Flow

The validation pipeline runs deterministically in order:

```text
Raw AI Output → Normalization → Parsing → Schema Validation → Constraint Validation → GuardResult
```

- **Provider-agnostic** — works with any LLM, agent framework, or custom AI system
- **Lightweight & Fast** — zero cloud dependencies, databases, or external services
- **Predictable Pipeline** — deterministic flow stopping at the first failing stage
- **Structured Errors** — detailed error objects with field, code, and message attributes
- **Pydantic Integration** — native schema validation using Pydantic models or types

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/ai_output_guard

# Lint and format check
ruff check src/ tests/
```

## License

MIT License