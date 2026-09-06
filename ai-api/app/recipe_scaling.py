from __future__ import annotations

from fractions import Fraction
import re

from app.schemas import RecipeImportDraft


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twenty-one": 21,
    "twenty-two": 22,
    "twenty-three": 23,
    "twenty-four": 24,
}
_NUMBER_PATTERN = "|".join(sorted((re.escape(value) for value in _NUMBER_WORDS), key=len, reverse=True))
_SERVING_PATTERNS = (
    re.compile(
        rf"\b(?:(?:serves?|for|to)\s+)?(?P<count>\d{{1,2}}|{_NUMBER_PATTERN})\s+"
        r"(?:servings?|people|portions?)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:servings?|yield)\s*(?::|=|to)?\s*(?P<count>\d{{1,2}}|{_NUMBER_PATTERN})\b",
        flags=re.IGNORECASE,
    ),
)
_SERVING_ONLY_WORDS = frozenset(
    {
        "a",
        "and",
        "change",
        "double",
        "doubled",
        "eight",
        "for",
        "halve",
        "half",
        "it",
        "make",
        "ok",
        "please",
        "people",
        "portion",
        "portions",
        "recipe",
        "scale",
        "serve",
        "serves",
        "serving",
        "servings",
        "the",
        "this",
        "to",
        "yield",
    }
    | set(_NUMBER_WORDS)
)
_UNICODE_FRACTIONS = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}
_QUANTITY_NUMBER = re.compile(r"(?<![\w.])(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)(?![\w.])")


def requested_serving_count(message: str, current_servings: int | None = None) -> int | None:
    normalized = message.casefold().replace("–", "-").replace("—", "-")
    for pattern in _SERVING_PATTERNS:
        match = pattern.search(normalized)
        if match:
            raw = match.group("count")
            count = int(raw) if raw.isdigit() else _NUMBER_WORDS.get(raw)
            return count if count is not None and 1 <= count <= 24 else None

    if current_servings and re.search(r"\b(?:double|doubled)\b", normalized):
        doubled = current_servings * 2
        return doubled if doubled <= 24 else None
    if current_servings and re.search(r"\b(?:halve|half)\b", normalized):
        halved = current_servings / 2
        return int(halved) if halved.is_integer() and halved >= 1 else None
    return None


def is_serving_only_change(message: str, current_servings: int | None = None) -> bool:
    if requested_serving_count(message, current_servings) is None:
        return False
    words = set(re.findall(r"[a-z]+(?:-[a-z]+)?|\d+", message.casefold()))
    return all(word.isdigit() or word in _SERVING_ONLY_WORDS for word in words)


def is_additive_serving_change(message: str, current_servings: int | None = None) -> bool:
    normalized = message.casefold()
    if requested_serving_count(message, current_servings) is None:
        return False
    if not re.search(r"\b(?:add|include)\b", normalized):
        return False
    return not re.search(r"\b(?:remove|omit|without|replace|swap|instead)\b", normalized)


def scale_recipe_draft(
    previous: RecipeImportDraft,
    candidate: RecipeImportDraft,
    target_servings: int,
) -> RecipeImportDraft:
    current_servings = previous.servings or 4
    ratio = Fraction(target_servings, current_servings)
    scaled_ingredients = [
        ingredient.model_copy(
            update={
                "quantity": scale_quantity_text(ingredient.quantity, ratio),
                "note": _update_serving_note(ingredient.note, target_servings),
            }
        )
        for ingredient in previous.ingredients
    ]
    return candidate.model_copy(
        update={
            "title": previous.title,
            "description": previous.description,
            "servings": target_servings,
            "ingredients": scaled_ingredients,
            "tags": list(previous.tags),
            "source": previous.source,
        },
        deep=True,
    )


def scale_additive_recipe_draft(
    previous: RecipeImportDraft,
    candidate: RecipeImportDraft,
    target_servings: int,
) -> RecipeImportDraft:
    """Scale established ingredients while retaining provider-added ingredients."""

    current_servings = previous.servings or 4
    ratio = Fraction(target_servings, current_servings)
    candidate_ratio = Fraction(target_servings, candidate.servings or current_servings)
    previous_names = [_ingredient_key(item.name) for item in previous.ingredients]
    scaled_existing = [
        ingredient.model_copy(
            update={
                "quantity": scale_quantity_text(ingredient.quantity, ratio),
                "note": _update_serving_note(ingredient.note, target_servings),
            }
        )
        for ingredient in previous.ingredients
    ]
    additions = [
        ingredient.model_copy(
            update={
                "quantity": scale_quantity_text(ingredient.quantity, candidate_ratio),
                "note": _update_serving_note(ingredient.note, target_servings),
            }
        )
        for ingredient in candidate.ingredients
        if not any(_ingredient_names_match(_ingredient_key(ingredient.name), name) for name in previous_names)
    ]
    return candidate.model_copy(
        update={
            "servings": target_servings,
            "ingredients": scaled_existing + additions,
        },
        deep=True,
    )


def draft_contains_ingredient(draft: RecipeImportDraft, ingredient: str) -> bool:
    requested = _ingredient_key(ingredient)
    return any(
        _ingredient_names_match(requested, _ingredient_key(item.name))
        for item in draft.ingredients
    )


def scale_quantity_text(value: str | None, ratio: Fraction) -> str | None:
    if value is None or ratio == 1:
        return value
    normalized = value
    for symbol, fraction in _UNICODE_FRACTIONS.items():
        normalized = normalized.replace(symbol, f" {fraction}")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    def replace(match: re.Match[str]) -> str:
        return _format_fraction(_parse_fraction(match.group(1)) * ratio)

    return _QUANTITY_NUMBER.sub(replace, normalized)


def _parse_fraction(value: str) -> Fraction:
    if " " in value:
        whole, fraction = value.split(maxsplit=1)
        return Fraction(int(whole), 1) + Fraction(fraction)
    return Fraction(value)


def _format_fraction(value: Fraction) -> str:
    value = value.limit_denominator(8)
    whole, remainder = divmod(value.numerator, value.denominator)
    if remainder == 0:
        return str(whole)
    fraction = f"{remainder}/{value.denominator}"
    return f"{whole} {fraction}" if whole else fraction


def _update_serving_note(note: str | None, target_servings: int) -> str | None:
    if note is None:
        return None
    return re.sub(
        r"\bfor\s+(?:\d{1,2}|[a-z]+(?:-[a-z]+)?)\s+servings\b",
        f"for {target_servings} servings",
        note,
        flags=re.IGNORECASE,
    )


def _ingredient_key(value: str) -> str:
    words = re.findall(r"[a-z]+", value.casefold())
    return " ".join(word[:-2] if word.endswith("es") else word[:-1] if word.endswith("s") else word for word in words)


def _ingredient_names_match(left: str, right: str) -> bool:
    if left == right:
        return True
    left_words = set(left.split())
    right_words = set(right.split())
    return bool(left_words and right_words and (left_words <= right_words or right_words <= left_words))
