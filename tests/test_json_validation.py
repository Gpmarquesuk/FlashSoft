import json
from pathlib import Path

import pytest

from utils.json_validation import (
    SchemaValidationError,
    load_schema,
    validate_plan,
)


def test_load_schema_from_json_string():
    schema_text = json.dumps(
        {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
    )
    schema = load_schema(schema_text)
    assert schema["required"] == ["name"]


def test_load_schema_from_file(tmp_path: Path):
    schema_file = tmp_path / "schema.json"
    schema_content = {
        "type": "object",
        "properties": {"enabled": {"type": "boolean", "default": True}},
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    schema = load_schema(schema_file)
    assert schema["properties"]["enabled"]["default"] is True


def test_load_schema_invalid_json_raises_value_error():
    with pytest.raises(ValueError):
        load_schema("{invalid json}")


def test_validate_plan_applies_defaults_without_mutating_original():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "flags": {
                "type": "object",
                "properties": {"feature_x": {"type": "boolean", "default": False}},
            },
        },
        "required": ["name"],
    }

    plan = {"name": "Architect"}
    normalized = validate_plan(plan, schema)

    assert normalized is not plan
    assert normalized["flags"]["feature_x"] is False
    assert "flags" not in plan


def test_validate_plan_raises_schema_validation_error_with_path():
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    with pytest.raises(SchemaValidationError) as excinfo:
        validate_plan({"name": 123}, schema)

    assert "name" in str(excinfo.value)


def test_validate_plan_invalid_schema_raises_value_error():
    invalid_schema = {
        "type": "object",
        "additionalProperties": "not_allowed",
    }

    with pytest.raises(ValueError) as excinfo:
        validate_plan({}, json.dumps(invalid_schema))

    assert "Invalid JSON schema" in str(excinfo.value)
