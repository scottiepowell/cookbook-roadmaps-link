from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas import RecipeImportDraft


@dataclass(frozen=True)
class RevisionIdentityCheck:
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


def _draft_tokens(draft: RecipeImportDraft) -> set[str]:
    parts = [draft.title, draft.description or ""]
    parts.extend(item.name for item in draft.ingredients)
    parts.extend(item.text for item in draft.instructions)
    return _tokens(" ".join(parts))


def _tokens(value: str) -> set[str]:
    # Exact word tokens intentionally distinguish "rice" from "riced cauliflower".
    return set(re.findall(r"[a-z]+", value.casefold()))
