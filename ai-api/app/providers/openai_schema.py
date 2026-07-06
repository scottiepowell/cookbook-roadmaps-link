from __future__ import annotations

from copy import deepcopy
from typing import Any


def normalize_strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return an OpenAI strict structured-output compatible schema copy."""
    normalized = deepcopy(schema)
    _normalize_node(normalized)
    return normalized


def _normalize_node(node: Any) -> None:
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            node["additionalProperties"] = False
            node["required"] = list(properties.keys())

        for value in node.values():
            _normalize_node(value)
    elif isinstance(node, list):
        for item in node:
            _normalize_node(item)
