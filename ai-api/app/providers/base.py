from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMRequest(BaseModel):
    prompt: str
    system: str | None = None
    max_output_tokens: int | None = Field(default=None, ge=1, le=4000)
    temperature: float | None = Field(default=None, ge=0, le=2)


class LLMResponse(BaseModel):
    text: str
    provider: str
    model: str
    usage: dict[str, int] | None = None


class StructuredLLMRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    schema_name: str
    schema_: dict[str, Any] = Field(alias="schema")
    system: str | None = None
    max_output_tokens: int | None = Field(default=None, ge=1, le=4000)

    @property
    def schema(self) -> dict[str, Any]:
        return self.schema_


class StructuredLLMResponse(BaseModel):
    data: dict[str, Any]
    provider: str
    model: str
    usage: dict[str, int] | None = None


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def generate_text(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        raise NotImplementedError
