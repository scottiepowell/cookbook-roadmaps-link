from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ProviderConfig(BaseModel):
    configured: bool


class ConfigResponse(BaseModel):
    providers: dict[str, ProviderConfig]


class RecipeDocument(BaseModel):
    id: str
    title: str
    description: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RecipeSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)


class RecipeSearchResult(BaseModel):
    id: str
    title: str
    score: int
    matched_fields: list[str] = Field(default_factory=list)
    snippet: str | None = None


class RecipeSearchResponse(BaseModel):
    query: str
    count: int
    results: list[RecipeSearchResult] = Field(default_factory=list)
