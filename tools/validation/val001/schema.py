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
    "uniqueItems", "minLength", "pattern", "minimum", "maximum", "title", "description",
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
    for key in ("$schema", "$id", "title", "description", "pattern"):
        if key in schema and not isinstance(schema[key], str):
            _fail(path, f"{key} must be a string")
    if "$schema" in schema and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
        _fail(path, "unsupported $schema dialect")
    if "$id" in schema and re.fullmatch(r"espresso\.val001\..+", schema["$id"]) is None:
        _fail(path, "invalid repository schema identifier")
    if "type" in schema:
        allowed_types = {"object", "array", "string", "integer", "number", "boolean", "null"}
        values = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not values or any(value not in allowed_types for value in values):
            _fail(path, f"unsupported schema type {schema['type']!r}")
    if "required" in schema:
        required=schema["required"]
        if not isinstance(required,list) or any(not isinstance(item,str) for item in required):
            _fail(path,"required must be an array of strings")
        if len(required)!=len(set(required)):
            _fail(path,"required names must be unique")
        if "properties" in schema and any(item not in schema["properties"] for item in required):
            _fail(path,"required name is not declared in properties")
    if "properties" in schema and not isinstance(schema["properties"],dict):
        _fail(path,"properties must be an object")
    for key, child in schema.get("properties", {}).items():
        if not isinstance(key,str): _fail(path,"property names must be strings")
        lint_schema(child, f"{path}.properties.{key}")
    if "items" in schema:
        if not isinstance(schema["items"],dict): _fail(path,"items must be a schema object")
        lint_schema(schema["items"], f"{path}.items")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"],bool):
        _fail(path,"additionalProperties must be boolean in the supported subset")
    if "enum" in schema:
        enum=schema["enum"]
        if not isinstance(enum,list) or not enum: _fail(path,"enum must be a nonempty array")
        rendered=[repr(item) for item in enum]
        if len(rendered)!=len(set(rendered)): _fail(path,"enum values must be unique")
    if "anyOf" in schema and (not isinstance(schema["anyOf"],list) or not schema["anyOf"]):
        _fail(path,"anyOf must be a nonempty array")
    for index, child in enumerate(schema.get("anyOf", [])):
        lint_schema(child, f"{path}.anyOf[{index}]")
    for key in ("minItems","maxItems","minLength"):
        if key in schema and (not isinstance(schema[key],int) or isinstance(schema[key],bool) or schema[key]<0):
            _fail(path,f"{key} must be a nonnegative integer")
    if "minItems" in schema and "maxItems" in schema and schema["minItems"]>schema["maxItems"]:
        _fail(path,"minItems exceeds maxItems")
    for key in ("minimum","maximum"):
        if key in schema and (not isinstance(schema[key],(int,float)) or isinstance(schema[key],bool) or not math.isfinite(schema[key])):
            _fail(path,f"{key} must be a finite number")
    if "minimum" in schema and "maximum" in schema and schema["minimum"]>schema["maximum"]:
        _fail(path,"minimum exceeds maximum")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"],bool):
        _fail(path,"uniqueItems must be boolean")
    if "pattern" in schema:
        try: re.compile(schema["pattern"])
        except re.error as exc: _fail(path,f"invalid pattern: {exc}")


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
