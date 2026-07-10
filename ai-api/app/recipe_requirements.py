from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.dataset_normalization import extract_phrases, normalize_text, safe_tokenize
from app.input_quality import REJECTED, classify_recipe_import_input


class RecipeRequirementSource(StrEnum):
    USER_PROVIDED = "user-provided"
    INFERRED = "inferred"
    DEFAULTED = "defaulted"
    RAG_SUPPORTED = "RAG-supported"
    CLARIFIED_BY_USER = "clarified-by-user"


class RecipeRequirementConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"


class RecipeSessionResponseState(StrEnum):
    DRAFT_GENERATED = "draft_generated"
    CLARIFICATION_NEEDED = "clarification_needed"
    RAG_REFRESHED = "rag_refreshed"
    DRAFT_REVISED = "draft_revised"
    NO_MATERIAL_CHANGE = "no_material_change"
    READY_TO_FINALIZE = "ready_to_finalize"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"


class RecipeFollowUpLabel(StrEnum):
    RELEVANT_REQUIREMENT_UPDATE = "relevant_requirement_update"
    CLARIFICATION_ANSWER = "clarification_answer"
    CORRECTION_TO_ASSUMPTION = "correction_to_assumption"
    IRRELEVANT_CHATTER = "irrelevant_chatter"
    FORMATTING_ONLY = "formatting_only"
    REGENERATE_WITHOUT_NEW_REQUIREMENTS = "regenerate_without_new_requirements"
    SAVE_OR_FINALIZE_REQUEST = "save_or_finalize_request"
    UNKNOWN = "unknown"


class RecipeRequirementField(BaseModel):
    value: str | int
    source: RecipeRequirementSource = RecipeRequirementSource.USER_PROVIDED


class RecipeClarificationQuestion(BaseModel):
    id: str
    question: str
    reason: str


class RecipeResolvedQuestion(BaseModel):
    question: str
    answer: str
    resolved_at: datetime


class RecipeRetrievalSummary(BaseModel):
    query: str | None = None
    retrieved_count: int = 0
    top_titles: list[str] = Field(default_factory=list)
    relevance_category: str | None = None
    rag_refresh_reason: str | None = None


class RecipeRequirementsState(BaseModel):
    interaction_id: str | None = None
    original_user_text: str
    latest_user_text: str
    dish_intent: RecipeRequirementField | None = None
    serving_count: RecipeRequirementField | None = None
    required_ingredients: list[RecipeRequirementField] = Field(default_factory=list)
    optional_ingredients: list[RecipeRequirementField] = Field(default_factory=list)
    excluded_ingredients: list[RecipeRequirementField] = Field(default_factory=list)
    cooking_method: RecipeRequirementField | None = None
    equipment_constraints: list[RecipeRequirementField] = Field(default_factory=list)
    time_constraints: list[RecipeRequirementField] = Field(default_factory=list)
    dietary_constraints: list[RecipeRequirementField] = Field(default_factory=list)
    texture_or_style_goals: list[RecipeRequirementField] = Field(default_factory=list)
    assumptions: list[RecipeRequirementField] = Field(default_factory=list)
    requirement_sources: dict[str, list[str]] = Field(default_factory=dict)
    confidence_label: RecipeRequirementConfidence = RecipeRequirementConfidence.LOW
    open_questions: list[RecipeClarificationQuestion] = Field(default_factory=list)
    resolved_questions: list[RecipeResolvedQuestion] = Field(default_factory=list)
    revision_count: int = 0
    last_retrieval_summary: RecipeRetrievalSummary | None = None
    last_retrieval_cache_key: str | None = None
    last_support_level: str | None = None
    last_citation_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=60))


class RecipeSessionDecision(BaseModel):
    should_clarify: bool
    question: str | None = None
    reason: str
    confidence_label: RecipeRequirementConfidence


class RecipeFollowUpClassification(BaseModel):
    label: RecipeFollowUpLabel
    reason: str
    should_refresh_rag: bool = False
    provider_generation_likely_needed: bool = False
    clarification_may_be_needed: bool = False


class RecipeRagRefreshDecision(BaseModel):
    should_refresh_rag: bool
    reason: str
    changed_fields: list[str] = Field(default_factory=list)
    previous_summary: dict[str, Any] = Field(default_factory=dict)
    current_summary: dict[str, Any] = Field(default_factory=dict)


DISH_PATTERNS: tuple[tuple[str, str], ...] = (
    ("chicken and rice casserole", "chicken and rice casserole"),
    ("chicken rice casserole", "chicken and rice casserole"),
    ("carbonara", "carbonara"),
    ("cheesecake", "cheesecake"),
    ("omelette", "omelet"),
    ("omelet", "omelet"),
    ("casserole", "casserole"),
)

INGREDIENT_TERMS = (
    "cream of chicken soup",
    "cream of mushroom soup",
    "graham cracker crust",
    "cream cheese",
    "graham cracker",
    "black pepper",
    "pasta water",
    "heavy cream",
    "parmesan cheese",
    "cheddar cheese",
    "melted butter",
    "olive oil",
    "brown sugar",
    "spaghetti",
    "parmesan",
    "pancetta",
    "ricotta",
    "vanilla",
    "chicken",
    "cheddar",
    "onions",
    "onion",
    "butter",
    "sugar",
    "eggs",
    "egg",
    "rice",
    "nuts",
)

GENERIC_DISH_TERMS = {"dessert", "dinner", "meal", "food", "recipe"}
SOCIAL_PHRASES = {"thanks", "thank you", "looks good", "great", "nice", "ok", "okay"}
FORMAT_PHRASES = {"shorter", "make it shorter", "bullet", "bullets", "table", "format", "rewrite", "concise"}
REGENERATE_PHRASES = {"regenerate", "try again", "redo", "generate again", "start over"}
FINALIZE_PHRASES = {"save", "save this", "finalize", "looks good save", "accept", "done"}
MATERIAL_FIELDS = (
    "dish_intent",
    "cooking_method",
    "required_ingredients",
    "excluded_ingredients",
    "dietary_constraints",
    "equipment_constraints",
    "time_constraints",
)


def extract_recipe_requirements(
    text: str | None,
    *,
    interaction_id: str | None = None,
    now: datetime | None = None,
    default_ttl_minutes: int = 60,
) -> RecipeRequirementsState:
    current_time = now or datetime.now(UTC)
    raw = text or ""
    normalized = normalize_text(raw)
    input_quality = classify_recipe_import_input(raw)

    state = RecipeRequirementsState(
        interaction_id=interaction_id,
        original_user_text=raw,
        latest_user_text=raw,
        created_at=current_time,
        updated_at=current_time,
        expires_at=current_time + timedelta(minutes=default_ttl_minutes),
    )
    if input_quality.status == REJECTED:
        if _is_vague_but_clarifiable(normalized):
            state.confidence_label = RecipeRequirementConfidence.LOW
            _refresh_requirement_sources(state)
            return state
        state.confidence_label = RecipeRequirementConfidence.REJECTED
        _refresh_requirement_sources(state)
        return state

    state.dish_intent = _extract_dish_intent(normalized)
    state.serving_count = _extract_serving_count(raw)
    if state.serving_count is None:
        state.serving_count = RecipeRequirementField(value=4, source=RecipeRequirementSource.DEFAULTED)
        state.assumptions.append(
            RecipeRequirementField(value="Default servings are 4 when not specified.", source=RecipeRequirementSource.DEFAULTED)
        )
    state.excluded_ingredients = _extract_excluded_ingredients(normalized)
    state.required_ingredients = _extract_required_ingredients(normalized, state.excluded_ingredients)
    state.cooking_method = _extract_cooking_method(normalized)
    state.equipment_constraints = _extract_equipment_constraints(normalized)
    state.time_constraints = _extract_time_constraints(normalized)
    state.dietary_constraints = _extract_dietary_constraints(normalized)
    state.texture_or_style_goals = _extract_style_goals(normalized)
    state.confidence_label = _confidence_for_state(state, normalized)
    _refresh_requirement_sources(state)
    return state


def decide_clarification(
    state: RecipeRequirementsState,
    *,
    retrieval_support_level: str | None = None,
) -> RecipeSessionDecision:
    if state.confidence_label == RecipeRequirementConfidence.REJECTED:
        return RecipeSessionDecision(
            should_clarify=False,
            reason="Input was rejected by deterministic quality checks.",
            confidence_label=state.confidence_label,
        )
    normalized = normalize_text(state.latest_user_text)
    if _is_social_chatter(normalized):
        return RecipeSessionDecision(
            should_clarify=False,
            reason="Message is social chatter, not a recipe requirement.",
            confidence_label=state.confidence_label,
        )
    if _is_formatting_only(normalized):
        return RecipeSessionDecision(
            should_clarify=False,
            reason="Message is formatting-only and does not affect recipe requirements.",
            confidence_label=state.confidence_label,
        )
    if state.dish_intent is None or state.confidence_label == RecipeRequirementConfidence.LOW:
        return RecipeSessionDecision(
            should_clarify=True,
            question="What dish do you want to make, and what main ingredients should it include?",
            reason="Dish intent is unclear or too broad for useful retrieval.",
            confidence_label=state.confidence_label,
        )
    conflict = _ingredient_conflict(state)
    if conflict:
        return RecipeSessionDecision(
            should_clarify=True,
            question=f"Should this recipe include {conflict}, or should it be excluded?",
            reason="A required ingredient conflicts with an excluded ingredient.",
            confidence_label=state.confidence_label,
        )
    if _has_chicken_casserole_safety_ambiguity(state, normalized):
        return RecipeSessionDecision(
            should_clarify=True,
            question="Is the chicken already cooked, or should the recipe start with raw chicken?",
            reason="Chicken handling affects safe casserole instructions.",
            confidence_label=state.confidence_label,
        )
    if retrieval_support_level == "weak" and state.dish_intent and len(state.required_ingredients) < 2:
        return RecipeSessionDecision(
            should_clarify=True,
            question="What main ingredient or style should guide this recipe?",
            reason="Retrieved examples were weak and the missing detail is user-specific.",
            confidence_label=state.confidence_label,
        )
    return RecipeSessionDecision(
        should_clarify=False,
        reason="Requirements are specific enough to proceed with safe assumptions.",
        confidence_label=state.confidence_label,
    )


def classify_follow_up(
    message: str,
    *,
    current_state: RecipeRequirementsState | None = None,
) -> RecipeFollowUpClassification:
    normalized = normalize_text(message)
    if not normalized:
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.UNKNOWN,
            reason="Follow-up message is empty.",
            clarification_may_be_needed=True,
        )
    if _is_social_chatter(normalized):
        return RecipeFollowUpClassification(label=RecipeFollowUpLabel.IRRELEVANT_CHATTER, reason="Message is social chatter.")
    if _is_finalize_request(normalized):
        return RecipeFollowUpClassification(label=RecipeFollowUpLabel.SAVE_OR_FINALIZE_REQUEST, reason="User asked to save or finalize.")
    if _is_regenerate_request(normalized):
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.REGENERATE_WITHOUT_NEW_REQUIREMENTS,
            reason="User asked to regenerate without adding requirements.",
            provider_generation_likely_needed=True,
        )
    if _is_formatting_only(normalized):
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.FORMATTING_ONLY,
            reason="User asked for formatting or wording only.",
            provider_generation_likely_needed=True,
        )
    if current_state and current_state.open_questions and _looks_like_clarification_answer(normalized):
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.CLARIFICATION_ANSWER,
            reason="Message appears to answer the open clarification question.",
            should_refresh_rag=True,
            provider_generation_likely_needed=True,
        )
    if _corrects_assumption(normalized):
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.CORRECTION_TO_ASSUMPTION,
            reason="User corrected a previous assumption.",
            should_refresh_rag=True,
            provider_generation_likely_needed=True,
        )
    if _has_material_update_signal(normalized):
        return RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.RELEVANT_REQUIREMENT_UPDATE,
            reason="User changed a retrieval-affecting recipe requirement.",
            should_refresh_rag=True,
            provider_generation_likely_needed=True,
        )
    return RecipeFollowUpClassification(
        label=RecipeFollowUpLabel.UNKNOWN,
        reason="Message was not confidently classified.",
        clarification_may_be_needed=True,
    )


def decide_rag_refresh(
    previous_state: RecipeRequirementsState,
    current_state: RecipeRequirementsState,
    *,
    follow_up: RecipeFollowUpClassification | None = None,
) -> RecipeRagRefreshDecision:
    previous_summary = summarize_retrieval_requirements(previous_state)
    current_summary = summarize_retrieval_requirements(current_state)
    if follow_up and follow_up.label in {
        RecipeFollowUpLabel.IRRELEVANT_CHATTER,
        RecipeFollowUpLabel.FORMATTING_ONLY,
        RecipeFollowUpLabel.REGENERATE_WITHOUT_NEW_REQUIREMENTS,
        RecipeFollowUpLabel.SAVE_OR_FINALIZE_REQUEST,
    }:
        return RecipeRagRefreshDecision(
            should_refresh_rag=False,
            reason=f"No RAG refresh for {follow_up.label.value}.",
            previous_summary=previous_summary,
            current_summary=current_summary,
        )

    changed_fields = [
        field
        for field in MATERIAL_FIELDS
        if previous_summary.get(field) != current_summary.get(field)
    ]
    previous_servings = previous_summary.get("serving_count")
    current_servings = current_summary.get("serving_count")
    if previous_servings and current_servings and abs(int(current_servings) - int(previous_servings)) >= 4:
        changed_fields.append("serving_count")

    if changed_fields:
        return RecipeRagRefreshDecision(
            should_refresh_rag=True,
            reason=f"RAG refresh required because {', '.join(changed_fields)} changed.",
            changed_fields=_dedupe(changed_fields),
            previous_summary=previous_summary,
            current_summary=current_summary,
        )
    return RecipeRagRefreshDecision(
        should_refresh_rag=False,
        reason="No retrieval-affecting requirements changed.",
        previous_summary=previous_summary,
        current_summary=current_summary,
    )


def summarize_retrieval_requirements(state: RecipeRequirementsState) -> dict[str, Any]:
    return {
        "dish_intent": _field_value(state.dish_intent),
        "serving_count": _field_value(state.serving_count),
        "required_ingredients": _field_values(state.required_ingredients),
        "excluded_ingredients": _field_values(state.excluded_ingredients),
        "cooking_method": _field_value(state.cooking_method),
        "equipment_constraints": _field_values(state.equipment_constraints),
        "time_constraints": _field_values(state.time_constraints),
        "dietary_constraints": _field_values(state.dietary_constraints),
    }


def _extract_dish_intent(normalized: str) -> RecipeRequirementField | None:
    for pattern, value in DISH_PATTERNS:
        if _contains_phrase(normalized, pattern):
            return RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED)
    return None


def _extract_serving_count(text: str) -> RecipeRequirementField | None:
    patterns = (
        r"\bfor\s+(\d{1,2})\b",
        r"\bserves\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+servings?\b",
        r"\bservings?\s*[:=]?\s*(\d{1,2})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = int(match.group(1))
            if 1 <= value <= 24:
                return RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED)
    return None


def _extract_required_ingredients(
    normalized: str,
    excluded_ingredients: list[RecipeRequirementField],
) -> list[RecipeRequirementField]:
    excluded = {str(item.value) for item in excluded_ingredients}
    values: list[str] = []
    phrase_values = set(extract_phrases(normalized))
    for term in INGREDIENT_TERMS:
        canonical = _canonical_ingredient(term)
        if canonical in excluded:
            continue
        if _contains_phrase(normalized, term) or canonical in phrase_values:
            values.append(canonical)
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in _dedupe(values)]


def _extract_excluded_ingredients(normalized: str) -> list[RecipeRequirementField]:
    values: list[str] = []
    for term in INGREDIENT_TERMS:
        canonical = _canonical_ingredient(term)
        if (
            _contains_phrase(normalized, f"no {term}")
            or _contains_phrase(normalized, f"without {term}")
            or _contains_phrase(normalized, f"omit {term}")
        ):
            values.append(canonical)
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in _dedupe(values)]


def _extract_cooking_method(normalized: str) -> RecipeRequirementField | None:
    methods: list[str] = []
    if _contains_phrase(normalized, "no bake") or _contains_phrase(normalized, "no-bake"):
        methods.append("no-bake")
    elif _contains_any(normalized, {"bake", "baked", "oven"}):
        methods.append("baked")
    if _contains_any(normalized, {"stovetop", "stove"}):
        methods.append("stovetop")
    if _contains_phrase(normalized, "slow cooker"):
        methods.append("slow cooker")
    if _contains_phrase(normalized, "air fryer"):
        methods.append("air fryer")
    if _contains_any(normalized, {"skillet", "pan"}):
        methods.append("skillet")
    if _contains_any(normalized, {"chill", "chilled", "overnight"}):
        methods.append("chill")
    if not methods:
        return None
    return RecipeRequirementField(value=", ".join(_dedupe(methods)), source=RecipeRequirementSource.USER_PROVIDED)


def _extract_equipment_constraints(normalized: str) -> list[RecipeRequirementField]:
    equipment = []
    for term in ("air fryer", "instant pot", "slow cooker", "skillet", "oven"):
        if _contains_phrase(normalized, term):
            equipment.append(term)
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in _dedupe(equipment)]


def _extract_time_constraints(normalized: str) -> list[RecipeRequirementField]:
    values: list[str] = []
    if match := re.search(r"\bunder\s+(\d{1,3})\s+minutes?\b", normalized):
        values.append(f"under {match.group(1)} minutes")
    if _contains_phrase(normalized, "overnight"):
        values.append("overnight")
    if _contains_phrase(normalized, "make ahead"):
        values.append("make-ahead")
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in _dedupe(values)]


def _extract_dietary_constraints(normalized: str) -> list[RecipeRequirementField]:
    values: list[str] = []
    for term in ("gluten free", "gluten-free", "vegetarian", "dairy free", "dairy-free", "low sodium", "low-sodium"):
        if _contains_phrase(normalized, term):
            values.append(term.replace("-", " "))
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in _dedupe(values)]


def _extract_style_goals(normalized: str) -> list[RecipeRequirementField]:
    values: list[str] = []
    for term in ("classic", "creamy", "crispy", "fluffy", "firm", "bubbly"):
        if _contains_phrase(normalized, term):
            values.append(term)
    return [RecipeRequirementField(value=value, source=RecipeRequirementSource.USER_PROVIDED) for value in values]


def _confidence_for_state(state: RecipeRequirementsState, normalized: str) -> RecipeRequirementConfidence:
    tokens = safe_tokenize(normalized)
    if not tokens:
        return RecipeRequirementConfidence.REJECTED
    if state.dish_intent is None:
        if set(tokens) & GENERIC_DISH_TERMS:
            return RecipeRequirementConfidence.LOW
        return RecipeRequirementConfidence.LOW
    detail_count = (
        len(state.required_ingredients)
        + len(state.excluded_ingredients)
        + len(state.dietary_constraints)
        + len(state.equipment_constraints)
        + (1 if state.cooking_method else 0)
    )
    if detail_count >= 3:
        return RecipeRequirementConfidence.HIGH
    return RecipeRequirementConfidence.MEDIUM


def _refresh_requirement_sources(state: RecipeRequirementsState) -> None:
    source_map: dict[str, list[str]] = {source.value: [] for source in RecipeRequirementSource}

    def add(field_name: str, value: RecipeRequirementField | list[RecipeRequirementField] | None) -> None:
        if value is None:
            return
        fields = value if isinstance(value, list) else [value]
        for field in fields:
            if field_name not in source_map[field.source.value]:
                source_map[field.source.value].append(field_name)

    add("dish_intent", state.dish_intent)
    add("serving_count", state.serving_count)
    add("required_ingredients", state.required_ingredients)
    add("optional_ingredients", state.optional_ingredients)
    add("excluded_ingredients", state.excluded_ingredients)
    add("cooking_method", state.cooking_method)
    add("equipment_constraints", state.equipment_constraints)
    add("time_constraints", state.time_constraints)
    add("dietary_constraints", state.dietary_constraints)
    add("texture_or_style_goals", state.texture_or_style_goals)
    add("assumptions", state.assumptions)
    state.requirement_sources = {key: values for key, values in source_map.items() if values}


def _has_material_update_signal(normalized: str) -> bool:
    if _contains_any(normalized, {"actually", "instead", "change", "use", "make"}):
        if (
            _extract_dish_intent(normalized)
            or _extract_cooking_method(normalized)
            or _extract_equipment_constraints(normalized)
            or _extract_dietary_constraints(normalized)
            or _extract_excluded_ingredients(normalized)
            or _extract_required_ingredients(normalized, [])
        ):
            return True
    return bool(
        _contains_phrase(normalized, "air fryer")
        or _contains_phrase(normalized, "no bake")
        or _contains_phrase(normalized, "gluten free")
        or _contains_phrase(normalized, "without")
    )


def _looks_like_clarification_answer(normalized: str) -> bool:
    return len(safe_tokenize(normalized)) <= 8 or _has_material_update_signal(normalized)


def _corrects_assumption(normalized: str) -> bool:
    return _contains_any(normalized, {"instead", "i meant", "not"}) and _has_material_update_signal(normalized)


def _ingredient_conflict(state: RecipeRequirementsState) -> str | None:
    required = {str(field.value) for field in state.required_ingredients}
    excluded = {str(field.value) for field in state.excluded_ingredients}
    overlap = sorted(required & excluded)
    return overlap[0] if overlap else None


def _has_chicken_casserole_safety_ambiguity(state: RecipeRequirementsState, normalized: str) -> bool:
    dish = str(_field_value(state.dish_intent) or "")
    if "chicken" not in dish and not _contains_phrase(normalized, "chicken"):
        return False
    if "casserole" not in dish and not _contains_phrase(normalized, "casserole"):
        return False
    return not (_contains_phrase(normalized, "cooked chicken") or _contains_phrase(normalized, "raw chicken"))


def _is_social_chatter(normalized: str) -> bool:
    return normalized in SOCIAL_PHRASES or normalized.startswith("thanks ") or normalized.startswith("thank you")


def _is_vague_but_clarifiable(normalized: str) -> bool:
    return normalized in {"make dessert", "dessert", "make dinner", "make meal"} or (
        _contains_any(normalized, GENERIC_DISH_TERMS) and len(safe_tokenize(normalized)) <= 3
    )


def _is_formatting_only(normalized: str) -> bool:
    return any(_contains_phrase(normalized, phrase) for phrase in FORMAT_PHRASES)


def _is_regenerate_request(normalized: str) -> bool:
    return any(_contains_phrase(normalized, phrase) for phrase in REGENERATE_PHRASES)


def _is_finalize_request(normalized: str) -> bool:
    return any(_contains_phrase(normalized, phrase) for phrase in FINALIZE_PHRASES)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(normalize_text(phrase))}(?!\w)", text) is not None


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(_contains_phrase(text, term) for term in terms)


def _canonical_ingredient(term: str) -> str:
    normalized = normalize_text(term)
    aliases = {
        "eggs": "egg",
        "onions": "onion",
        "graham crackers": "graham cracker",
        "melted butter": "butter",
        "cheddar cheese": "cheddar",
        "parmesan cheese": "parmesan",
        "cream soup": "cream of chicken soup",
    }
    return aliases.get(normalized, normalized)


def _field_value(field: RecipeRequirementField | None) -> str | int | None:
    return field.value if field else None


def _field_values(fields: list[RecipeRequirementField]) -> list[str | int]:
    return [field.value for field in fields]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
