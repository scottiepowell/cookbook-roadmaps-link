from pydantic import ValidationError

from app.ai_access_models import AiAccessWorkflow
from app.ai_budget_guard import check_provider_budget
from app.config import get_ai_settings
from app.config import get_provider_budget_settings
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_meal_plan_preferences
from app.meal_planner import (
    build_no_match_meal_plan_response,
    deterministic_partial_meal_plan,
    select_meal_plan_candidates,
)
from app.providers import LLMProvider, StructuredLLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.recipe_reader import load_recipe_documents
from app.schemas import MealPlanDraft, MealPlanRequest, MealPlanResponse, MealPlanSelectionMetadata


MEAL_PLAN_SYSTEM_PROMPT = (
    "Create a meal plan using only the selected saved recipe candidates. "
    "Every meal must cite a provided recipe ID and title. "
    "Do not invent external recipes, shopping lists, nutrition analysis, calories, macros, or medical claims. "
    "If there are fewer candidates than requested slots, return a partial plan using saved recipes only."
)


class MealPlanError(RuntimeError):
    """Base error for meal-plan endpoint failures."""


class MealPlanProviderError(MealPlanError):
    """Raised when the provider cannot generate a meal-plan draft."""


class MealPlanValidationError(MealPlanError):
    """Raised when provider output is not a valid saved-recipe meal plan."""


def create_meal_plan(
    request: MealPlanRequest,
    provider: LLMProvider | None = None,
    session_state: object | None = None,
) -> MealPlanResponse:
    settings = get_ai_settings()
    input_quality = classify_meal_plan_preferences(_meal_plan_quality_text(request))
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return MealPlanResponse(
            plan=MealPlanDraft(days=[]),
            citations=[],
            provider="none",
            model="none",
            selection=MealPlanSelectionMetadata(
                candidate_count=0,
                matched_recipe_ids=[],
                requested_slots=request.days * request.meals_per_day,
            ),
            warnings=input_quality.warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    foundation_request = _foundation_request(request)
    recipes = load_recipe_documents()
    foundation = select_meal_plan_candidates(recipes, foundation_request)

    if not foundation.candidates:
        response = build_no_match_meal_plan_response(request, foundation)
        response.input_quality = input_quality.to_dict()
        if input_quality.status == WEAK_BUT_USABLE:
            response.warnings = [*input_quality.warnings, *response.warnings]
        return response

    provider_name = provider.name if provider is not None else settings.provider
    provider_model = getattr(provider, "model", None)
    if provider_model is None:
        provider_model = settings.openai_model if provider_name == "openai" else settings.model
    budget_decision = check_provider_budget(
        AiAccessWorkflow.MEAL_PLAN,
        provider_name,
        provider_model,
        _estimate_input_tokens(request, foundation.candidates),
        settings.max_output_tokens,
        session_state,
        get_provider_budget_settings(),
    )
    if not budget_decision.allowed:
        warnings = [*foundation.warnings]
        if input_quality.status == WEAK_BUT_USABLE:
            warnings.extend(input_quality.warnings)
        warnings.append(budget_decision.safe_message)
        return MealPlanResponse(
            plan=deterministic_partial_meal_plan(request, foundation.candidates),
            citations=foundation.candidates,
            provider="none",
            model="none",
            selection=MealPlanSelectionMetadata(
                candidate_count=len(foundation.candidates),
                matched_recipe_ids=[candidate.recipe_id for candidate in foundation.candidates],
                requested_slots=request.days * request.meals_per_day,
            ),
            warnings=warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )
    active_provider = provider or _get_configured_provider()
    try:
        provider_response = active_provider.generate_structured(
            StructuredLLMRequest(
                prompt=_build_prompt(request, foundation.candidates),
                system=MEAL_PLAN_SYSTEM_PROMPT,
                schema_name="MealPlanDraft",
                schema=MealPlanDraft.model_json_schema(),
                max_output_tokens=settings.max_output_tokens,
            )
        )
    except ProviderError as exc:
        raise MealPlanProviderError("Meal-plan provider failed.") from exc

    try:
        provider_plan = MealPlanDraft.model_validate(provider_response.data)
    except ValidationError as exc:
        raise MealPlanValidationError("Provider returned an invalid meal plan.") from exc

    plan = _coerce_to_saved_candidates(provider_plan, request, foundation.candidates)
    warnings = [*foundation.warnings]
    if input_quality.status == WEAK_BUT_USABLE:
        warnings.extend(input_quality.warnings)
    if _planned_meal_count(plan) < request.days * request.meals_per_day:
        warnings.append("Meal plan is partial because there were fewer saved recipe candidates than requested slots.")

    return MealPlanResponse(
        plan=plan,
        citations=foundation.candidates,
        provider=provider_response.provider,
        model=provider_response.model,
        selection=MealPlanSelectionMetadata(
            candidate_count=len(foundation.candidates),
            matched_recipe_ids=[candidate.recipe_id for candidate in foundation.candidates],
            requested_slots=request.days * request.meals_per_day,
        ),
        warnings=warnings,
        usage=provider_response.usage,
        input_quality=input_quality.to_dict(),
    )


def _foundation_request(request: MealPlanRequest) -> MealPlanRequest:
    query = request.query or request.preferences
    include_tags = [*request.include_tags, *request.tags]
    return MealPlanRequest(
        days=request.days,
        meals_per_day=request.meals_per_day,
        query=query,
        preferences=request.preferences,
        include_tags=include_tags,
        tags=request.tags,
        exclude_ingredients=request.exclude_ingredients,
        candidate_limit=request.candidate_limit,
    )


def _meal_plan_quality_text(request: MealPlanRequest) -> str | None:
    parts = [
        request.preferences or "",
        request.query or "",
        " ".join(request.include_tags),
        " ".join(request.tags),
    ]
    text = " ".join(part for part in parts if part).strip()
    return text or None


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise MealPlanProviderError("Meal-plan provider is not configured.") from exc


def _build_prompt(request: MealPlanRequest, candidates: list) -> str:
    candidate_blocks = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_blocks.append(
            "\n".join(
                [
                    f"[{index}] Recipe ID: {candidate.recipe_id}",
                    f"Title: {candidate.title}",
                    f"Snippet: {candidate.snippet}",
                ]
            )
        )
    return "\n".join(
        [
            f"Days: {request.days}",
            f"Meals per day: {request.meals_per_day}",
            f"Preferences: {request.preferences or request.query or ''}",
            f"Tags: {', '.join([*request.include_tags, *request.tags])}",
            "Selected saved recipe candidates:",
            "\n\n".join(candidate_blocks),
        ]
    )


def _coerce_to_saved_candidates(
    provider_plan: MealPlanDraft,
    request: MealPlanRequest,
    candidates,
) -> MealPlanDraft:
    candidate_by_id = {candidate.recipe_id: candidate for candidate in candidates}
    used_ids: set[str] = set()
    days = []
    for day in provider_plan.days:
        meals = []
        for meal in day.meals:
            candidate = candidate_by_id.get(meal.recipe_id)
            if candidate is None or candidate.recipe_id in used_ids:
                continue
            meals.append(
                meal.model_copy(
                    update={
                        "recipe_id": candidate.recipe_id,
                        "title": candidate.title,
                    }
                )
            )
            used_ids.add(candidate.recipe_id)
        days.append(day.model_copy(update={"meals": meals}))

    cleaned = MealPlanDraft(days=days)
    if _planned_meal_count(cleaned) == 0:
        return deterministic_partial_meal_plan(request, candidates)
    return cleaned


def _planned_meal_count(plan: MealPlanDraft) -> int:
    return sum(len(day.meals) for day in plan.days)


def _estimate_input_tokens(request: MealPlanRequest, candidates: list) -> int:
    prompt = _build_prompt(request, candidates)
    return max(1, len(prompt.split()))
