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


class DatasetSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    dataset_limit: int | None = Field(default=None, ge=1, le=5000)


class DatasetIndexSummaryResponse(BaseModel):
    document_count: int
    source_counts: dict[str, int] = Field(default_factory=dict)
    fields_indexed: list[str] = Field(default_factory=list)
    token_count: int
    build_metadata: dict[str, str | int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class InputQualityResponse(BaseModel):
    status: str
    reason: str
    clarifying_question: str | None = None
    warnings: list[str] = Field(default_factory=list)


class DatasetSearchProvenance(BaseModel):
    dataset: str = "Food Ingredients and Recipes Dataset with Images"
    creator: str = "pes12017000148"
    license: str = "CC BY-SA 3.0"
    license_url: str = "https://creativecommons.org/licenses/by-sa/3.0/"
    source_url: str = "https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images"
    source_file: str
    source_table: str | None = None
    source_id: str


class DatasetSearchResult(BaseModel):
    id: str
    source_id: str
    title: str
    score: int
    matched_fields: list[str] = Field(default_factory=list)
    snippet: str | None = None
    source_file: str
    source_table: str | None = None
    provenance: DatasetSearchProvenance


class DatasetSearchResponse(BaseModel):
    query: str
    count: int
    results: list[DatasetSearchResult] = Field(default_factory=list)
    index: DatasetIndexSummaryResponse
    warnings: list[str] = Field(default_factory=list)
    input_quality: InputQualityResponse | None = None


class DatasetAskRequest(BaseModel):
    question: str
    limit: int = Field(default=3, ge=1, le=10)
    dataset_limit: int | None = Field(default=None, ge=1, le=5000)


class DatasetAskCitation(BaseModel):
    id: str
    source_id: str
    title: str
    snippet: str
    matched_fields: list[str] = Field(default_factory=list)
    provenance: DatasetSearchProvenance


class DatasetAskRetrievalMetadata(BaseModel):
    query: str
    retrieved_count: int
    limit: int
    dataset_limit: int
    matched_result_ids: list[str] = Field(default_factory=list)
    index: DatasetIndexSummaryResponse


class DatasetAskResponse(BaseModel):
    answer: str
    citations: list[DatasetAskCitation] = Field(default_factory=list)
    provider: str
    model: str
    retrieval: DatasetAskRetrievalMetadata
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int] | None = None
    input_quality: InputQualityResponse | None = None


class RecipeImportRequest(BaseModel):
    text: str
    source: str | None = None


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
    servings: int | None = Field(default=4, ge=1, le=24)
    ingredients: list[RecipeIngredientDraft] = Field(min_length=1)
    instructions: list[RecipeInstructionDraft] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None


class RecipeImportCitation(BaseModel):
    id: str
    source_id: str
    title: str
    snippet: str
    matched_fields: list[str] = Field(default_factory=list)
    provenance: DatasetSearchProvenance


class RecipeImportRetrievalMetadata(BaseModel):
    query: str
    retrieved_count: int
    limit: int
    dataset_limit: int
    matched_result_ids: list[str] = Field(default_factory=list)
    anchors_used: list[str] = Field(default_factory=list)
    matched_result_scores: list[int] = Field(default_factory=list)
    relevance_category: str | None = None
    warning: str | None = None
    index: DatasetIndexSummaryResponse | None = None


class RecipeImportResponse(BaseModel):
    draft: RecipeImportDraft | None = None
    provider: str
    model: str
    retrieval: RecipeImportRetrievalMetadata | None = None
    citations: list[RecipeImportCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int] | None = None
    input_quality: InputQualityResponse | None = None


class AskRequest(BaseModel):
    question: str
    limit: int = Field(default=3, ge=1, le=10)


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
    input_quality: InputQualityResponse | None = None


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


class MealPlanRequest(MealPlanFoundationRequest):
    preferences: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("preferences")
    @classmethod
    def normalize_blank_preferences(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            stripped = item.strip().lower()
            if stripped and stripped not in normalized:
                normalized.append(stripped)
        return normalized


class MealPlanSlot(BaseModel):
    slot: str = Field(min_length=1)
    recipe_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class MealPlanDay(BaseModel):
    day: int = Field(ge=1)
    meals: list[MealPlanSlot] = Field(default_factory=list)


class MealPlanDraft(BaseModel):
    days: list[MealPlanDay] = Field(default_factory=list)


class MealPlanSelectionMetadata(BaseModel):
    candidate_count: int
    matched_recipe_ids: list[str] = Field(default_factory=list)
    requested_slots: int


class MealPlanResponse(BaseModel):
    plan: MealPlanDraft
    citations: list[MealPlanRecipeReference] = Field(default_factory=list)
    provider: str
    model: str
    selection: MealPlanSelectionMetadata
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int] | None = None
    input_quality: InputQualityResponse | None = None
