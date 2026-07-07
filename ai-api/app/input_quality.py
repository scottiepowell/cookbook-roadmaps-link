from __future__ import annotations

import re
from dataclasses import dataclass, field


READY = "ready"
WEAK_BUT_USABLE = "weak_but_usable"
NEEDS_CLARIFICATION = "needs_clarification"
REJECTED = "rejected"

DEFAULT_MAX_INPUT_CHARS = 4000
QUESTION_MAX_INPUT_CHARS = 500
SEARCH_MAX_INPUT_CHARS = 200

PLACEHOLDER_INPUTS = {
    "asdf",
    "asdfasdf",
    "asdfasdfasdf",
    "foo",
    "food",
    "recipe",
    "stuff",
    "test",
    "todo",
    "unknown",
}

VAGUE_IMPORTER_INPUTS = {
    "make food",
    "healthy meal",
    "recipe for stuff i have",
}

VAGUE_QUESTION_INPUTS = {
    "make food",
    "healthy meal",
    "what should i make",
    "recipe for stuff i have",
}

VAGUE_MEAL_PLAN_INPUTS = {
    "plan dinner",
    "make dinner",
    "healthy meal",
    "make food",
    "recipe for stuff i have",
}

COOKING_TERMS = {
    "bake",
    "baked",
    "beans",
    "boil",
    "breakfast",
    "chicken",
    "cook",
    "cucumber",
    "dinner",
    "garlic",
    "herb",
    "lemon",
    "lunch",
    "meal",
    "olive",
    "onion",
    "oven",
    "pasta",
    "parsley",
    "recipe",
    "rice",
    "roast",
    "salad",
    "sauce",
    "skillet",
    "slow",
    "soup",
    "stir",
    "tomato",
    "toast",
    "weeknight",
}

MEAL_SLOT_TERMS = {"breakfast", "lunch", "dinner", "snack", "full-day", "day", "meal"}


@dataclass(frozen=True)
class InputQualityResult:
    status: str
    reason: str
    clarifying_question: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "clarifying_question": self.clarifying_question,
            "warnings": self.warnings,
        }


def classify_recipe_import_input(text: str | None) -> InputQualityResult:
    base = _classify_common(text, max_chars=DEFAULT_MAX_INPUT_CHARS, purpose="recipe or cooking notes")
    if base.status != READY:
        return base

    normalized = _normalize(text)
    tokens = _tokens(text)
    if normalized in VAGUE_IMPORTER_INPUTS:
        return InputQualityResult(
            NEEDS_CLARIFICATION,
            "Input does not include enough recipe detail to extract a grounded draft.",
            "What ingredients and cooking method should I use for this recipe draft?",
        )
    if len(tokens) < 4 and not _has_cooking_signal(tokens):
        return _rejected("Input does not contain recognizable recipe details.", "Please include at least one ingredient or cooking method.")
    if len(tokens) < 8:
        return InputQualityResult(
            WEAK_BUT_USABLE,
            "Input is short but includes enough cooking detail to try a bounded draft.",
            warnings=["Assuming missing quantities and timing are unspecified."],
        )
    return InputQualityResult(READY, "Input is specific enough to process.")


def classify_question_input(question: str | None) -> InputQualityResult:
    base = _classify_common(question, max_chars=QUESTION_MAX_INPUT_CHARS, purpose="cookbook question")
    if base.status != READY:
        return base

    normalized = _normalize(question)
    tokens = _tokens(question)
    if normalized in VAGUE_QUESTION_INPUTS or (len(tokens) <= 2 and not _has_cooking_signal(tokens)):
        return InputQualityResult(
            NEEDS_CLARIFICATION,
            "Question does not include enough saved-recipe search detail.",
            "What ingredient, recipe name, or meal goal should I search your saved recipes for?",
        )
    if len(tokens) <= 3:
        return InputQualityResult(
            WEAK_BUT_USABLE,
            "Question is brief, so retrieval may rely on a narrow keyword match.",
            warnings=["Using the short question as the saved-recipe search query."],
        )
    return InputQualityResult(READY, "Question is specific enough to process.")


def classify_dataset_search_input(query: str | None) -> InputQualityResult:
    base = _classify_common(query, max_chars=SEARCH_MAX_INPUT_CHARS, purpose="dataset search query")
    if base.status != READY:
        return base

    normalized = _normalize(query)
    tokens = _tokens(query)
    if normalized in {"recipe for stuff i have", "make food", "healthy meal"}:
        return InputQualityResult(
            NEEDS_CLARIFICATION,
            "Dataset search query is too broad to rank useful recipe records.",
            "Which ingredient, dish name, or cooking style should I search for?",
        )
    if len(tokens) == 1 and tokens[0] not in COOKING_TERMS:
        return InputQualityResult(
            WEAK_BUT_USABLE,
            "Dataset search query is narrow and may return few matches.",
            warnings=["Using the single keyword as the dataset search query."],
        )
    return InputQualityResult(READY, "Dataset search query is specific enough to process.")


def classify_dataset_question_input(question: str | None) -> InputQualityResult:
    result = classify_question_input(question)
    if result.status == NEEDS_CLARIFICATION:
        return InputQualityResult(
            NEEDS_CLARIFICATION,
            "Dataset question does not include enough indexed-recipe search detail.",
            "Which ingredient, dish name, or dataset recipe topic should I search for?",
        )
    return result


def classify_meal_plan_preferences(preferences: str | None) -> InputQualityResult:
    base = _classify_common(preferences, max_chars=QUESTION_MAX_INPUT_CHARS, purpose="meal-planning preferences")
    if base.status != READY:
        return base

    normalized = _normalize(preferences)
    tokens = _tokens(preferences)
    if normalized in VAGUE_MEAL_PLAN_INPUTS or (
        set(tokens) <= {"plan", "meal", "meals", "food"} and "plan" in {token.lower() for token in tokens}
    ):
        return InputQualityResult(
            NEEDS_CLARIFICATION,
            "Meal-plan preferences do not include enough meal scope or ingredient detail.",
            "Do you want breakfast, lunch, dinner, or a full-day plan?",
        )
    if len(tokens) <= 2 and not (set(tokens) & MEAL_SLOT_TERMS):
        return InputQualityResult(
            WEAK_BUT_USABLE,
            "Meal-plan preferences are brief, so the plan will use narrow saved-recipe matching.",
            warnings=["Assuming the provided terms are the main meal-planning preference."],
        )
    return InputQualityResult(READY, "Meal-plan preferences are specific enough to process.")


def _classify_common(text: str | None, *, max_chars: int, purpose: str) -> InputQualityResult:
    raw = text or ""
    stripped = raw.strip()
    if not stripped:
        return _rejected(f"Input is empty for {purpose}.", "Please enter a short ingredient, recipe, question, or meal goal.")
    if len(stripped) > max_chars:
        return _rejected(f"Input is longer than the {max_chars} character limit.", f"Please shorten this to {max_chars} characters or fewer.")
    if not any(char.isalpha() for char in stripped):
        return _rejected(f"Input does not contain alphabetical {purpose} details.", "Please include at least one ingredient, recipe name, or cooking goal.")
    if _mostly_symbols(stripped):
        return _rejected("Input is mostly symbols and cannot be used safely.", "Please replace symbols with a plain-language cooking request.")
    if _repeated_junk(stripped):
        return _rejected("Input appears to be repeated junk text.", "Please include a real ingredient, dish name, or meal goal.")

    normalized = _normalize(stripped)
    tokens = _tokens(stripped)
    if normalized in PLACEHOLDER_INPUTS:
        return _rejected("Input looks like placeholder text.", "Please include at least one ingredient, recipe name, or cooking method.")
    if len(tokens) == 1 and len(tokens[0]) < 3:
        return _rejected("Input is too short to produce a grounded result.", "Please add one ingredient, dish name, or meal goal.")
    return InputQualityResult(READY, "Input passed basic deterministic checks.")


def _rejected(reason: str, guidance: str) -> InputQualityResult:
    return InputQualityResult(REJECTED, reason, None, [guidance])


def _tokens(text: str | None) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z'-]*", text or "").copy()


def _normalize(text: str | None) -> str:
    return " ".join(token.lower().strip("'") for token in _tokens(text))


def _has_cooking_signal(tokens: list[str]) -> bool:
    return bool({token.lower() for token in tokens} & COOKING_TERMS)


def _mostly_symbols(text: str) -> bool:
    non_space = [char for char in text if not char.isspace()]
    if not non_space:
        return False
    symbol_count = sum(1 for char in non_space if not char.isalnum())
    return symbol_count / len(non_space) >= 0.6


def _repeated_junk(text: str) -> bool:
    normalized = _normalize(text)
    compact = re.sub(r"\s+", "", normalized)
    if len(compact) >= 8 and len(set(compact)) <= 3:
        return True
    return compact in {"asdfasdf", "asdfasdfasdf", "qwertyqwerty", "blahblahblah"}
