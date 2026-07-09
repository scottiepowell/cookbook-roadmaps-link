import json
import os
from typing import Any

from app.config import DEFAULT_AI_MAX_OUTPUT_TOKENS, DEFAULT_OPENAI_FALLBACK_MODEL, DEFAULT_OPENAI_MODEL
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.providers.errors import ProviderCallError, ProviderConfigError, build_provider_call_error
from app.providers.openai_schema import normalize_strict_json_schema


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_OPENAI_MODEL,
        fallback_model: str = DEFAULT_OPENAI_FALLBACK_MODEL,
        max_output_tokens: int = DEFAULT_AI_MAX_OUTPUT_TOKENS,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        if not self.api_key or not self.api_key.strip():
            raise ProviderConfigError("OpenAI provider selected but OPENAI_API_KEY is not configured.")

        self.model = model
        self.fallback_model = fallback_model
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds
        self._client = None

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        try:
            response = self._client_instance().responses.create(
                model=self.model,
                input=self._input_messages(request.prompt, request.system),
                max_output_tokens=request.max_output_tokens or self.max_output_tokens,
                temperature=request.temperature,
            )
        except Exception as exc:  # pragma: no cover - live provider path is manual-only.
            raise build_provider_call_error("OpenAI text generation failed.", exc) from exc

        return LLMResponse(
            text=_response_text(response),
            provider=self.name,
            model=self.model,
            usage=_response_usage(response),
        )

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        try:
            response = self._client_instance().responses.create(
                model=self.model,
                input=self._input_messages(request.prompt, request.system),
                max_output_tokens=request.max_output_tokens or self.max_output_tokens,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": request.schema_name,
                        "schema": normalize_strict_json_schema(request.schema),
                        "strict": True,
                    }
                },
            )
        except Exception as exc:  # pragma: no cover - live provider path is manual-only.
            raise build_provider_call_error("OpenAI structured generation failed.", exc) from exc

        text = _response_text(response)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - live provider path is manual-only.
            raise ProviderCallError(
                "OpenAI structured generation returned invalid JSON.",
                failure_category="invalid_json",
                exception_type=exc.__class__.__name__,
                safe_summary="Structured response could not be decoded as JSON.",
            ) from exc

        return StructuredLLMResponse(
            data=data,
            provider=self.name,
            model=self.model,
            usage=_response_usage(response),
        )

    def _client_instance(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - dependency is installed in validation.
                raise ProviderConfigError("OpenAI provider requires the openai Python package.") from exc
            self._client = OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)
        return self._client

    @staticmethod
    def _input_messages(prompt: str, system: str | None) -> list[dict[str, str]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text
    return str(response)


def _response_usage(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None

    values: dict[str, int] = {}
    for source_name, target_name in (
        ("input_tokens", "input_tokens"),
        ("output_tokens", "output_tokens"),
        ("total_tokens", "total_tokens"),
    ):
        value = getattr(usage, source_name, None)
        if isinstance(value, int):
            values[target_name] = value
    return values or None
