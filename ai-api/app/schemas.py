from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.ai_access_models import AiAccessGrant, AiAdminAuditEvent, AiBudgetSnapshot, AiDemoSession


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
    provider_mode: str | None = None
    model: str | None = None


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
    provider_mode: str | None = None
    model: str | None = None


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


class RecipeImportContextPackingMetadata(BaseModel):
    packed_count: int = 0
    packed_ids: list[str] = Field(default_factory=list)
    dropped_ids: list[str] = Field(default_factory=list)
    max_examples: int = 0
    max_context_chars: int = 0
    packed_context_chars: int = 0
    weak_examples_included: bool = False
    context_budget_warning: str | None = None


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
    packed_count: int = 0
    packed_ids: list[str] = Field(default_factory=list)
    dropped_ids: list[str] = Field(default_factory=list)
    max_examples: int = 0
    max_context_chars: int = 0
    packed_context_chars: int = 0
    weak_examples_included: bool = False
    context_budget_warning: str | None = None
    support_level: str | None = None
    support_reason: str | None = None
    citation_support_count: int = 0
    weak_citation_count: int = 0
    strong_citation_count: int = 0
    support_message: str | None = None
    should_claim_rag_grounded: bool = False
    should_show_weak_support_warning: bool = False
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


class RecipeSessionStartRequest(BaseModel):
    text: str
    source: str | None = None
    provider_mode: str | None = None
    model: str | None = None


class RecipeSessionMessageRequest(BaseModel):
    text: str
    provider_mode: str | None = None
    model: str | None = None


class RecipeSessionFinalizeRequest(BaseModel):
    format: str | None = None


class RecipeRequirementValueResponse(BaseModel):
    value: str | int
    source: str


class RecipeSessionRequirementsResponse(BaseModel):
    dish_intent: RecipeRequirementValueResponse | None = None
    serving_count: RecipeRequirementValueResponse | None = None
    required_ingredients: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    optional_ingredients: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    excluded_ingredients: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    cooking_method: RecipeRequirementValueResponse | None = None
    equipment_constraints: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    time_constraints: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    dietary_constraints: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    texture_or_style_goals: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    assumptions: list[RecipeRequirementValueResponse] = Field(default_factory=list)
    requirement_sources: dict[str, list[str]] = Field(default_factory=dict)
    confidence_label: str
    open_questions: list[str] = Field(default_factory=list)
    resolved_questions: list[dict[str, str]] = Field(default_factory=list)


class RecipeSessionDecisionResponse(BaseModel):
    should_clarify: bool | None = None
    question: str | None = None
    reason: str | None = None
    confidence_label: str | None = None
    delta_label: str | None = None
    provider_generation_likely_needed: bool | None = None
    clarification_may_be_needed: bool | None = None


class RecipeSessionRetrievalSummary(BaseModel):
    query: str | None = None
    retrieved_count: int = 0
    top_titles: list[str] = Field(default_factory=list)
    relevance_category: str | None = None
    rag_refresh_reason: str | None = None


class RecipeSessionDraftSummary(BaseModel):
    title: str
    servings: int | None = None
    ingredient_count: int = 0
    instruction_count: int = 0


class RecipeSessionRequirementDiffResponse(BaseModel):
    changed_fields: list[str] = Field(default_factory=list)
    added_requirements: dict[str, list[str]] = Field(default_factory=dict)
    removed_requirements: dict[str, list[str]] = Field(default_factory=dict)
    updated_requirements: dict[str, str] = Field(default_factory=dict)
    summary_message: str
    rag_refresh_relevant: bool = False
    rag_refresh_reason: str | None = None
    previous_revision: int = 0
    current_revision: int = 0


class RecipeSessionApiResponse(BaseModel):
    interaction_id: str | None = None
    response_state: str
    requirements: RecipeSessionRequirementsResponse | None = None
    decision: RecipeSessionDecisionResponse | None = None
    clarification_question: str | None = None
    rag_refreshed: bool = False
    rag_refresh_reason: str | None = None
    changed_fields: list[str] = Field(default_factory=list)
    requirement_diff: RecipeSessionRequirementDiffResponse | None = None
    revision_summary: str | None = None
    draft: RecipeImportDraft | None = None
    draft_summary: RecipeSessionDraftSummary | None = None
    citations: list[RecipeImportCitation] = Field(default_factory=list)
    retrieval: RecipeImportRetrievalMetadata | None = None
    retrieval_summary: RecipeSessionRetrievalSummary | None = None
    support_level: str | None = None
    provider: str | None = None
    model: str | None = None
    revision_count: int = 0
    expires_at: str | None = None
    warnings: list[str] = Field(default_factory=list)


class AiInviteGrantCreateRequest(BaseModel):
    token: str | None = None
    allowed_workflows: list[str] = Field(default_factory=list)
    ttl_seconds: int | None = Field(default=None, ge=1, le=86400)
    max_sessions: int | None = Field(default=None, ge=1, le=10)
    max_provider_calls: int | None = Field(default=None, ge=0)
    max_estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None
    operator_label: str | None = None


class AiInviteGrantResponse(BaseModel):
    grant: AiAccessGrant
    invite_token: str | None = None
    session_count: int = 0
    active_session_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    audit_event: AiAdminAuditEvent | None = None


class AiInviteRedeemRequest(BaseModel):
    invite_token: str
    operator_label: str | None = None


class AiInviteSessionResponse(BaseModel):
    grant: AiAccessGrant
    session: AiDemoSession
    session_token: str | None = None
    budget_snapshot: AiBudgetSnapshot | None = None
    warnings: list[str] = Field(default_factory=list)
    audit_event: AiAdminAuditEvent | None = None


class AiInviteStatusResponse(BaseModel):
    enabled: bool
    configured: bool
    status: str
    message: str
    allowed_workflows: list[str] = Field(default_factory=list)
    local_operator_create_enabled: bool = True
    grant_ttl_seconds: int = 0
    session_ttl_seconds: int = 0
    max_sessions_per_grant: int = 0
    default_max_provider_calls: int = 0
    default_max_estimated_cost_usd: Decimal = Decimal("0.00")
    active_grants: int = 0
    active_sessions: int = 0
    warnings: list[str] = Field(default_factory=list)


class AskRequest(BaseModel):
    question: str
    limit: int = Field(default=3, ge=1, le=10)
    provider_mode: str | None = None
    model: str | None = None


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
    provider_mode: str | None = None
    model: str | None = None

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


class DatasetCacheMetadata(BaseModel):
    cache_enabled: bool = True
    index_cache_hit: bool | None = None
    retrieval_cache_hit: bool | None = None
    index_cache_key: str | None = None
    retrieval_cache_key: str | None = None
    cache_entry_count: int = 0
    cache_max_entries: int = 0
    cache_ttl_seconds: int | None = None
    cache_invalidated_reason: str | None = None


class DatasetIndexSummaryResponse(BaseModel):
    document_count: int
    source_counts: dict[str, int] = Field(default_factory=dict)
    fields_indexed: list[str] = Field(default_factory=list)
    token_count: int
    build_metadata: dict[str, str | int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    cache: DatasetCacheMetadata = Field(default_factory=DatasetCacheMetadata)


class DatasetSearchResponse(BaseModel):
    query: str
    count: int
    results: list[DatasetSearchResult] = Field(default_factory=list)
    index: DatasetIndexSummaryResponse
    warnings: list[str] = Field(default_factory=list)
    input_quality: InputQualityResponse | None = None
    cache: DatasetCacheMetadata = Field(default_factory=DatasetCacheMetadata)


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
    packed_count: int = 0
    packed_ids: list[str] = Field(default_factory=list)
    dropped_ids: list[str] = Field(default_factory=list)
    max_examples: int = 0
    max_context_chars: int = 0
    packed_context_chars: int = 0
    weak_examples_included: bool = False
    context_budget_warning: str | None = None
    support_level: str | None = None
    support_reason: str | None = None
    citation_support_count: int = 0
    weak_citation_count: int = 0
    strong_citation_count: int = 0
    support_message: str | None = None
    should_claim_rag_grounded: bool = False
    should_show_weak_support_warning: bool = False
    cache: DatasetCacheMetadata = Field(default_factory=DatasetCacheMetadata)
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
