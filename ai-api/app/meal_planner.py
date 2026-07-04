from app.schemas import (
    MealPlanCandidateSelectionMetadata,
    MealPlanDay,
    MealPlanDraft,
    MealPlanFoundationRequest,
    MealPlanFoundationResponse,
    MealPlanRequest,
    MealPlanResponse,
    MealPlanRecipeReference,
    MealPlanSelectionMetadata,
    MealPlanSlot,
    RecipeDocument,
)
from app.search import search_recipes


def select_meal_plan_candidates(
    recipes: list[RecipeDocument],
    request: MealPlanFoundationRequest,
) -> MealPlanFoundationResponse:
    requested_slots = request.days * request.meals_per_day
    warnings: list[str] = []
    excluded_recipe_ids: list[str] = []

    ranked = _rank_recipes(recipes, request)
    candidates: list[MealPlanRecipeReference] = []
    for recipe, matched_fields, snippet in ranked:
        if _has_excluded_ingredient(recipe, request.exclude_ingredients):
            excluded_recipe_ids.append(recipe.id)
            continue
        candidates.append(
            MealPlanRecipeReference(
                recipe_id=recipe.id,
                title=recipe.title,
                snippet=snippet or _recipe_snippet(recipe),
                matched_fields=matched_fields,
            )
        )
        if len(candidates) >= min(request.candidate_limit, requested_slots):
            break

    if excluded_recipe_ids:
        warnings.append("Some saved recipes were filtered because they matched excluded ingredients.")
    if len(candidates) < requested_slots:
        warnings.append("Fewer saved recipe candidates were found than requested meal slots.")

    return MealPlanFoundationResponse(
        candidates=candidates,
        selection=MealPlanCandidateSelectionMetadata(
            requested_slots=requested_slots,
            candidate_limit=request.candidate_limit,
            selected_count=len(candidates),
            excluded_recipe_ids=excluded_recipe_ids,
        ),
        warnings=warnings,
    )


def build_no_match_meal_plan_response(
    request: MealPlanRequest,
    foundation: MealPlanFoundationResponse,
) -> MealPlanResponse:
    warnings = [*foundation.warnings]
    warnings.append("No saved recipe candidates matched the meal-plan request; no provider call was made.")
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
        warnings=warnings,
        usage=None,
    )


def deterministic_partial_meal_plan(
    request: MealPlanRequest,
    candidates: list[MealPlanRecipeReference],
) -> MealPlanDraft:
    days: list[MealPlanDay] = []
    candidate_index = 0
    for day_number in range(1, request.days + 1):
        meals: list[MealPlanSlot] = []
        for meal_number in range(1, request.meals_per_day + 1):
            if candidate_index >= len(candidates):
                break
            candidate = candidates[candidate_index]
            meals.append(
                MealPlanSlot(
                    slot=f"meal {meal_number}",
                    recipe_id=candidate.recipe_id,
                    title=candidate.title,
                    reason="Selected from saved recipe candidates.",
                )
            )
            candidate_index += 1
        days.append(MealPlanDay(day=day_number, meals=meals))
    return MealPlanDraft(days=days)


def _rank_recipes(
    recipes: list[RecipeDocument],
    request: MealPlanFoundationRequest,
) -> list[tuple[RecipeDocument, list[str], str | None]]:
    query_parts = []
    if request.query and request.query.strip():
        query_parts.append(request.query.strip())
    query_parts.extend(tag.strip() for tag in request.include_tags if tag.strip())
    query = " ".join(query_parts)

    by_id = {recipe.id: recipe for recipe in recipes}
    if query:
        search_results = search_recipes(recipes, query=query, limit=len(recipes))
        ranked = []
        for result in search_results:
            recipe = by_id.get(result.id)
            if recipe is not None:
                ranked.append((recipe, result.matched_fields, result.snippet))
        return ranked

    return [(recipe, [], _recipe_snippet(recipe)) for recipe in recipes]


def _has_excluded_ingredient(recipe: RecipeDocument, excluded_ingredients: list[str]) -> bool:
    ingredient_text = " ".join(recipe.ingredients).lower()
    for excluded in excluded_ingredients:
        normalized = excluded.strip().lower()
        if normalized and normalized in ingredient_text:
            return True
    return False


def _recipe_snippet(recipe: RecipeDocument) -> str:
    parts = [recipe.description or "", " ".join(recipe.ingredients), " ".join(recipe.instructions)]
    snippet = " ".join(part for part in parts if part).strip()
    return snippet[:180] if snippet else recipe.title
