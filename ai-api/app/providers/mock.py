from typing import Any

from app.config import DEFAULT_AI_MODEL
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = DEFAULT_AI_MODEL) -> None:
        self.model = model

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        prompt = " ".join(request.prompt.split())
        preview = prompt[:80] if prompt else "empty prompt"
        return LLMResponse(
            text=f"Mock response from {self.model}: {preview}",
            provider=self.name,
            model=self.model,
            usage={"input_tokens": len(prompt.split()), "output_tokens": 6},
        )

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        data = _fixture_for_schema(request.schema, request.schema)
        data["_mock"] = {
            "schema_name": request.schema_name,
            "prompt_preview": " ".join(request.prompt.split())[:80],
        }
        return StructuredLLMResponse(
            data=data,
            provider=self.name,
            model=self.model,
            usage={"input_tokens": len(request.prompt.split()), "output_tokens": len(data)},
        )


def _fixture_for_schema(schema: dict[str, Any], root_schema: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root_schema or schema
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return {}

    required = schema.get("required")
    required_fields = set(required if isinstance(required, list) else properties.keys())
    return {
        key: _fixture_value(value, root)
        for key, value in properties.items()
        if key in required_fields
    }


def _fixture_value(schema: Any, root_schema: dict[str, Any]) -> Any:
    if not isinstance(schema, dict):
        return None

    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root_schema)

    value_type = schema.get("type")
    if isinstance(value_type, list):
        value_type = next((item for item in value_type if item != "null"), value_type[0])

    if value_type == "string":
        return "mock-value"
    if value_type == "integer":
        return 1
    if value_type == "number":
        return 1.0
    if value_type == "boolean":
        return False
    if value_type == "array":
        return [_fixture_value(schema.get("items", {"type": "string"}), root_schema)]
    if value_type == "object":
        return _fixture_for_schema(schema, root_schema)
    return None


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        return {}
    defs = root_schema.get("$defs")
    if not isinstance(defs, dict):
        return {}
    value = defs.get(ref.removeprefix(prefix))
    return value if isinstance(value, dict) else {}
