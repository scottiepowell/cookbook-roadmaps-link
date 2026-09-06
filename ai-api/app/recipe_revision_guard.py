from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas import RecipeImportDraft


@dataclass(frozen=True)
class RevisionIdentityCheck:
    valid: bool
    violation_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecipeCoherenceCheck:
    valid: bool
    violation_codes: tuple[str, ...] = ()


_IDENTITY_GROUPS: dict[str, frozenset[str]] = {
    "pasta": frozenset(
        {
            "pasta",
            "rigatoni",
            "spaghetti",
            "macaroni",
            "penne",
            "linguine",
            "fettuccine",
            "noodle",
            "noodles",
            "lasagna",
        }
    ),
    "rice": frozenset({"rice", "risotto"}),
    "tortilla": frozenset(
        {"enchilada", "enchiladas", "tortilla", "tortillas", "taco", "tacos", "burrito", "burritos"}
    ),
    "soup": frozenset({"soup", "stew", "chowder"}),
    "pizza": frozenset({"pizza"}),
    "potato": frozenset({"potato", "potatoes"}),
    "quinoa": frozenset({"quinoa"}),
    "chicken": frozenset({"chicken"}),
    "pork": frozenset({"pork"}),
    "beef": frozenset({"beef"}),
    "turkey": frozenset({"turkey"}),
    "tofu": frozenset({"tofu"}),
    "shrimp": frozenset({"shrimp"}),
    "salmon": frozenset({"salmon"}),
}
_EXPLICIT_CHANGE_WORDS = frozenset(
    {
        "replace",
        "replacing",
        "instead",
        "substitute",
        "substitution",
        "swap",
        "remove",
        "without",
        "omit",
        "switch",
    }
)

_PASTA_TERMS = _IDENTITY_GROUPS["pasta"]
_RICE_TERMS = _IDENTITY_GROUPS["rice"]
_PROTEIN_GROUPS = {
    group: terms
    for group, terms in _IDENTITY_GROUPS.items()
    if group in {"chicken", "pork", "beef", "turkey", "tofu", "shrimp", "salmon"}
}


def validate_recipe_revision(
    previous: RecipeImportDraft,
    candidate: RecipeImportDraft,
    requested_change: str,
) -> RevisionIdentityCheck:
    """Check only stable recipe-identity signals; never inspect provider metadata."""

    previous_all = _draft_tokens(previous)
    previous_instructions = _tokens(" ".join(item.text for item in previous.instructions))
    candidate_all = _draft_tokens(candidate)
    candidate_instructions = _tokens(" ".join(item.text for item in candidate.instructions))
    request_tokens = _tokens(requested_change)
    explicit_change = bool(request_tokens & _EXPLICIT_CHANGE_WORDS)
    violations: list[str] = []

    for group, terms in _IDENTITY_GROUPS.items():
        was_established = bool(previous_all & terms)
        if group == "rice" and {"riced", "cauliflower"} <= previous_all:
            # "Riced cauliflower" and "cauliflower rice" are equivalent wording,
            # but neither makes plain rice the base of the existing recipe.
            was_established = True
        was_instruction_anchor = bool(previous_instructions & terms)
        requested_group = bool(request_tokens & terms)
        may_change_group = requested_group and explicit_change

        if was_established and was_instruction_anchor and not may_change_group:
            if not candidate_instructions & terms:
                violations.append(f"missing_instruction_anchor:{group}")

        newly_introduced = not was_established and bool(candidate_all & terms)
        if newly_introduced and not requested_group:
            violations.append(f"unrequested_identity_anchor:{group}")

    return RevisionIdentityCheck(valid=not violations, violation_codes=tuple(sorted(set(violations))))


def validate_recipe_coherence(
    candidate: RecipeImportDraft,
    expected_recipe_text: str | None = None,
) -> RecipeCoherenceCheck:
    """Reject high-confidence title, ingredient, and instruction contradictions."""

    title = _tokens(" ".join(part for part in (candidate.title, expected_recipe_text or "") if part))
    ingredients = _tokens(" ".join(item.name for item in candidate.ingredients))
    instructions = _tokens(" ".join(item.text for item in candidate.instructions))
    violations: list[str] = []

    title_is_omelet = bool(title & {"omelet", "omelette"})
    stale_omelet_anchor = bool(instructions & {"omelet", "omelette"}) and "fold" in instructions
    if stale_omelet_anchor and not title_is_omelet:
        violations.append("stale_instruction_anchor:omelet")

    title_is_pasta = bool(title & _PASTA_TERMS)
    if title_is_pasta:
        if not instructions & _PASTA_TERMS:
            violations.append("missing_instruction_anchor:pasta")
        if "bake" in title and not instructions & {"bake", "baked", "baking", "oven"}:
            violations.append("missing_method_anchor:bake")

    title_is_fried_rice = "fried" in title and "rice" in title
    if title_is_fried_rice:
        if not instructions & _RICE_TERMS:
            violations.append("missing_instruction_anchor:rice")
        if not instructions & {"fry", "fried", "saute", "skillet", "stir", "wok"}:
            violations.append("missing_method_anchor:fried_rice")

    if title_is_pasta or title_is_fried_rice:
        for group, terms in _PROTEIN_GROUPS.items():
            if ingredients & terms and not instructions & terms:
                violations.append(f"unused_major_ingredient:{group}")

    return RecipeCoherenceCheck(valid=not violations, violation_codes=tuple(sorted(set(violations))))


def _draft_tokens(draft: RecipeImportDraft) -> set[str]:
    parts = [draft.title, draft.description or ""]
    parts.extend(item.name for item in draft.ingredients)
    parts.extend(item.text for item in draft.instructions)
    return _tokens(" ".join(parts))


def _tokens(value: str) -> set[str]:
    # Exact word tokens intentionally distinguish "rice" from "riced cauliflower".
    return set(re.findall(r"[a-z]+", value.casefold()))
