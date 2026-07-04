from app.schemas import (
    MealPlanCandidateSelectionMetadata,
    MealPlanFoundationRequest,
    MealPlanFoundationResponse,
    MealPlanRecipeReference,
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
