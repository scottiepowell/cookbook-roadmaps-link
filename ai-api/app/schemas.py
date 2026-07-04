from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class RecipeImportRequest(BaseModel):
    text: str = Field(min_length=1)
    source: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Recipe text must not be empty.")
        return value


class RecipeIngredientDraft(BaseModel):
    name: str = Field(min_length=1)
    quantity: str | None = None
    unit: str | None = None
    note: str | None = None


class RecipeInstructionDraft(BaseModel):
    step: int = Field(ge=1)
    text: str = Field(min_length=1)


class RecipeImportDraft(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    ingredients: list[RecipeIngredientDraft] = Field(min_length=1)
    instructions: list[RecipeInstructionDraft] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None


class RecipeImportResponse(BaseModel):
    draft: RecipeImportDraft
    provider: str
    model: str
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int] | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be empty.")
        return value


class AskCitation(BaseModel):
    recipe_id: str
    title: str
    snippet: str


class AskRetrievalMetadata(BaseModel):
    query: str
    retrieved_count: int
    limit: int
    matched_recipe_ids: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    citations: list[AskCitation] = Field(default_factory=list)
    provider: str
    model: str
    retrieval: AskRetrievalMetadata
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int] | None = None


class MealPlanFoundationRequest(BaseModel):
    days: int = Field(default=3, ge=1, le=14)
    meals_per_day: int = Field(default=1, ge=1, le=4)
    query: str | None = None
    include_tags: list[str] = Field(default_factory=list)
    exclude_ingredients: list[str] = Field(default_factory=list)
    candidate_limit: int = Field(default=10, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalize_blank_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("include_tags", "exclude_ingredients")
    @classmethod
    def normalize_string_list(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            stripped = item.strip().lower()
            if stripped and stripped not in normalized:
                normalized.append(stripped)
        return normalized


class MealPlanRecipeReference(BaseModel):
    recipe_id: str
    title: str
    snippet: str
    matched_fields: list[str] = Field(default_factory=list)


class MealPlanCandidateSelectionMetadata(BaseModel):
    requested_slots: int
    candidate_limit: int
    selected_count: int
    excluded_recipe_ids: list[str] = Field(default_factory=list)


class MealPlanFoundationResponse(BaseModel):
    candidates: list[MealPlanRecipeReference] = Field(default_factory=list)
    selection: MealPlanCandidateSelectionMetadata
    warnings: list[str] = Field(default_factory=list)
