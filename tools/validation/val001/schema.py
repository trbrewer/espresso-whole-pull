"""Small, dependency-free JSON-Schema subset used by governed VAL-001 records."""
from __future__ import annotations

import math
import re
from typing import Any


class SchemaError(ValueError):
    pass


ALLOWED_KEYWORDS = frozenset({
    "$schema", "$id", "type", "const", "enum", "anyOf", "required",
    "properties", "additionalProperties", "items", "minItems", "maxItems",
    "uniqueItems", "minLength", "pattern", "minimum", "maximum",
})


def _fail(path: str, message: str) -> None:
    raise SchemaError(f"{path}: {message}")


def lint_schema(schema: Any, path: str = "$") -> None:
    """Reject unsupported vocabulary before it can be silently ignored."""
    if not isinstance(schema, dict):
        _fail(path, "schema node must be an object")
    unknown = sorted(set(schema) - ALLOWED_KEYWORDS)
    if unknown:
        _fail(path, f"unsupported schema keywords {unknown}")
    if "type" in schema:
        allowed_types = {"object", "array", "string", "integer", "number", "boolean", "null"}
        values = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not values or any(value not in allowed_types for value in values):
            _fail(path, f"unsupported schema type {schema['type']!r}")
    for key, child in schema.get("properties", {}).items():
        lint_schema(child, f"{path}.properties.{key}")
    if "items" in schema:
        lint_schema(schema["items"], f"{path}.items")
    for index, child in enumerate(schema.get("anyOf", [])):
        lint_schema(child, f"{path}.anyOf[{index}]")


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate the deliberately small schema vocabulary used by VAL-001."""
    lint_schema(schema, path=f"{path}<schema>")
    if "const" in schema and instance != schema["const"]:
        _fail(path, f"expected constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        _fail(path, f"not in enum {schema['enum']!r}")
    if "anyOf" in schema:
        errors = []
        for candidate in schema["anyOf"]:
            try:
                validate(instance, candidate, path)
                break
            except SchemaError as exc:
                errors.append(str(exc))
        else:
            _fail(path, "did not match any allowed schema")
    expected = schema.get("type")
    if expected:
        checks = {
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
            "string": lambda x: isinstance(x, str),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "boolean": lambda x: isinstance(x, bool),
            "null": lambda x: x is None,
        }
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(checks[k](instance) for k in allowed):
            _fail(path, f"expected type {expected!r}")
    if isinstance(instance, float) and not math.isfinite(instance):
        _fail(path, "non-finite number")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            _fail(path, f"missing required properties {missing}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(instance) - set(props))
            if unknown:
                _fail(path, f"unknown properties {unknown}")
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], f"{path}.{key}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            _fail(path, "too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            _fail(path, "too many items")
        if schema.get("uniqueItems") and len({repr(x) for x in instance}) != len(instance):
            _fail(path, "duplicate items")
        if "items" in schema:
            for index, value in enumerate(instance):
                validate(value, schema["items"], f"{path}[{index}]")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            _fail(path, "string too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            _fail(path, f"does not match {schema['pattern']!r}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            _fail(path, "below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            _fail(path, "above maximum")
