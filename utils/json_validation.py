"""Utilities for validating Architect plans against JSON Schema definitions."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Union

from jsonschema import Draft7Validator, ValidationError
from jsonschema.exceptions import SchemaError
from jsonschema.validators import extend

SchemaSource = Union[str, Path, Mapping[str, Any]]


class SchemaValidationError(Exception):
    """Raised when a plan fails JSON schema validation."""


def load_schema(schema_source: SchemaSource) -> Mapping[str, Any]:
    """
    Load a JSON schema definition.

    Args:
        schema_source: JSON schema expressed as a mapping, JSON string, or filesystem path.

    Returns:
        The parsed schema as a dictionary.

    Raises:
        TypeError: If the schema source type is unsupported.
        ValueError: If the schema content cannot be parsed as JSON.
        FileNotFoundError: If a provided path does not exist.
        OSError: If there is an error reading from the provided path.
    """
    if isinstance(schema_source, Mapping):
        return json.loads(json.dumps(schema_source))

    if isinstance(schema_source, Path):
        schema_text = schema_source.read_text(encoding="utf-8")
    elif isinstance(schema_source, str):
        possible_path = Path(schema_source)
        if possible_path.exists() and possible_path.is_file():
            schema_text = possible_path.read_text(encoding="utf-8")
        else:
            schema_text = schema_source
    else:
        raise TypeError(
            "Unsupported schema source type. Expected str, pathlib.Path, or Mapping."
        )

    try:
        return json.loads(schema_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse JSON schema.") from exc


def _extend_with_default(validator_class: type[Draft7Validator]) -> type[Draft7Validator]:
    """
    Extend a jsonschema validator so that it sets default values on instances.
    """
    validate_properties = validator_class.VALIDATORS.get("properties", lambda *args: ())

    def set_defaults(validator, properties, instance, schema):
        if isinstance(instance, dict):
            for property_name, subschema in properties.items():
                if property_name not in instance:
                    if "default" in subschema:
                        instance[property_name] = deepcopy(subschema["default"])
                    elif subschema.get('type') == 'object' and "properties" in subschema:
                        instance[property_name] = {}
        yield from validate_properties(validator, properties, instance, schema)

    return extend(validator_class, {"properties": set_defaults})


DefaultValidatingDraft7Validator = _extend_with_default(Draft7Validator)


def validate_plan(plan_data: Any, schema_source: SchemaSource) -> Any:
    """
    Validate plan data against a JSON schema and return a normalized copy.

    Args:
        plan_data: Arbitrary JSON-like data representing the plan.
        schema_source: JSON schema expressed as a mapping, JSON string, or filesystem path.

    Returns:
        A deep-copied version of the plan augmented with schema defaults.

    Raises:
        SchemaValidationError: If validation fails.
        ValueError: If the provided schema is invalid.
    """
    schema = load_schema(schema_source)

    try:
        Draft7Validator.check_schema(schema)
        validator = DefaultValidatingDraft7Validator(schema)
    except SchemaError as exc:
        raise ValueError(f"Invalid JSON schema: {exc.message}") from exc

    normalized_data = deepcopy(plan_data)

    try:
        validator.validate(normalized_data)
    except ValidationError as exc:
        raise SchemaValidationError(_format_validation_error(exc)) from exc

    return normalized_data


def _format_validation_error(error: ValidationError) -> str:
    path = ".".join(str(element) for element in error.absolute_path)
    if path:
        return f"{error.message} (at path: {path})"
    return error.message
