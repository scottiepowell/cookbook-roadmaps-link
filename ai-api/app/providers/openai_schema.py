from __future__ import annotations

from copy import deepcopy
from typing import Any

STRIP_SCHEMA_METADATA_KEYS = {"default", "examples", "title", "description"}
SCHEMA_HINT_KEYS = {
    "$defs",
    "$ref",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "enum",
    "format",
    "items",
    "maximum",
    "maxItems",
    "maxLength",
    "minimum",
    "minItems",
    "minLength",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "type",
}


def normalize_strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return an OpenAI strict structured-output compatible schema copy."""
    normalized = deepcopy(schema)
    _normalize_node(normalized)
    return normalized


def _normalize_node(node: Any) -> None:
    if isinstance(node, dict):
        if _looks_like_schema_node(node):
            for key in STRIP_SCHEMA_METADATA_KEYS:
                node.pop(key, None)
        properties = node.get("properties")
        if isinstance(properties, dict):
            node["additionalProperties"] = False
            node["required"] = list(properties.keys())

        for value in node.values():
            _normalize_node(value)
    elif isinstance(node, list):
        for item in node:
            _normalize_node(item)


def _looks_like_schema_node(node: dict[str, Any]) -> bool:
    return any(key in SCHEMA_HINT_KEYS for key in node)
