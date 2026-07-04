import re
from dataclasses import dataclass

from app.schemas import RecipeDocument, RecipeSearchResult


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

FIELD_WEIGHTS = {
    "title": 10,
    "tags": 8,
    "ingredients": 5,
    "instructions": 3,
    "description": 2,
    "source": 1,
}


@dataclass(frozen=True)
class _ScoredRecipe:
    result: RecipeSearchResult
    original_index: int


def search_recipes(
    recipes: list[RecipeDocument],
    query: str,
    limit: int = 10,
) -> list[RecipeSearchResult]:
    query_tokens = _tokenize(query)
    if not query_tokens or limit <= 0:
        return []

    scored: list[_ScoredRecipe] = []
    for index, recipe in enumerate(recipes):
        result = _score_recipe(recipe, query_tokens)
        if result is not None:
            scored.append(_ScoredRecipe(result=result, original_index=index))

    scored.sort(key=lambda item: (-item.result.score, item.original_index))
    return [item.result for item in scored[:limit]]


def _score_recipe(recipe: RecipeDocument, query_tokens: list[str]) -> RecipeSearchResult | None:
    field_values = {
        "title": [recipe.title],
        "tags": recipe.tags,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "description": [recipe.description] if recipe.description else [],
        "source": [recipe.source] if recipe.source else [],
    }

    score = 0
    matched_fields: list[str] = []
    snippet: str | None = None

    for field, values in field_values.items():
        field_text = " ".join(value for value in values if value)
        if not field_text:
            continue

        field_tokens = _tokenize(field_text)
        field_score = sum(1 for token in query_tokens if _token_matches(token, field_tokens))
        if field_score == 0:
            continue

        score += field_score * FIELD_WEIGHTS[field]
        matched_fields.append(field)
        if snippet is None:
            snippet = _make_snippet(field_text, query_tokens)

    if score == 0:
        return None

    return RecipeSearchResult(
        id=recipe.id,
        title=recipe.title,
        score=score,
        matched_fields=matched_fields,
        snippet=snippet,
    )


def _tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


def _token_matches(query_token: str, field_tokens: list[str]) -> bool:
    return any(
        field_token == query_token
        or field_token.startswith(query_token)
        or query_token.startswith(field_token)
        for field_token in field_tokens
    )


def _make_snippet(value: str, query_tokens: list[str]) -> str:
    compact = " ".join(value.split())
    lowered = compact.lower()
    first_match = min(
        (lowered.find(token) for token in query_tokens if lowered.find(token) >= 0),
        default=0,
    )
    start = max(first_match - 40, 0)
    end = min(start + 140, len(compact))
    snippet = compact[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(compact):
        snippet = f"{snippet}..."
    return snippet
