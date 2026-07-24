"""Fixture-only contract for a future Cookbook recipe import adapter.

This module deliberately has no HTTP, database, filesystem, provider, or
authentication dependency.  It maps the validated sidecar importer draft into
an in-memory candidate and returns a dry-run result.  A future core Cookbook
adapter may use the contract after schema and authorization work is approved.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas import RecipeImportDraft


CONTRACT_VERSION = "cookbook-import.v1"
RECIPE_SCHEMA_VERSION = "cookbook-recipe-candidate.v1"
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2_000
MAX_NOTES_LENGTH = 4_000
MAX_SOURCE_LENGTH = 2_000
MAX_TAG_LENGTH = 80
MAX_TAGS = 30
MAX_INGREDIENTS = 100
MAX_INSTRUCTIONS = 100
MAX_FIELD_LENGTH = 2_000

_DRAFT_FIELDS = {
    "title",
    "description",
    "servings",
    "ingredients",
    "instructions",
    "tags",
    "source",
    "notes",
}
_INGREDIENT_FIELDS = {"name", "quantity", "unit", "note"}
_INSTRUCTION_FIELDS = {"step", "text"}


class CookbookIngredientPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    quantity: str | None = None
    unit: str | None = None
    note: str | None = None


class CookbookInstructionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=1)
    text: str = Field(min_length=1)


class CookbookRecipePayload(BaseModel):
    """Safe candidate shape, not a claim about the upstream write schema."""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    servings: int | None = None
    ingredients: list[CookbookIngredientPayload]
    instructions: list[CookbookInstructionPayload]
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None


class CookbookImportCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    idempotency_key: str
    contract_version: str
    schema_version: str
    ingredient_fingerprint: str
    payload: CookbookRecipePayload


class CookbookDuplicateCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    title: str
    match: Literal["title_and_ingredients"]


class CookbookFieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    code: str
    message: str


class CookbookIdempotencyMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    replayed: bool = False
    result_id: str


class CookbookImportDryRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["valid", "invalid", "duplicate", "idempotent_replay", "schema_mismatch"]
    contract_version: str
    schema_version: str
    candidate: CookbookImportCandidate | None = None
    errors: list[CookbookFieldError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duplicate_candidates: list[CookbookDuplicateCandidate] = Field(default_factory=list)
    idempotency: CookbookIdempotencyMetadata


class FakeCookbookRecipe(BaseModel):
    """Minimal existing-recipe fixture used only for duplicate checks."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    title: str
    ingredients: list[str] = Field(default_factory=list)


def _safe_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def _normalise_text(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value.strip()) or None


def _normalise_tag(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _unknown_fields(value: Mapping[str, Any], allowed: set[str], prefix: str) -> list[CookbookFieldError]:
    return [
        CookbookFieldError(
            field=f"{prefix}.{key}",
            code="unknown_field",
            message="Field is not accepted by the importer candidate contract.",
        )
        for key in sorted(set(value) - allowed)
    ]


def _validation_errors(exc: ValidationError) -> list[CookbookFieldError]:
    errors: list[CookbookFieldError] = []
    for item in exc.errors():
        location = ".".join(str(part) for part in item.get("loc", ())) or "candidate"
        code = str(item.get("type", "invalid_value"))
        errors.append(CookbookFieldError(field=location, code=code, message="Value does not satisfy the candidate contract."))
    return errors


def _source_errors(source: str | None) -> list[CookbookFieldError]:
    if not source or ":" not in source:
        return []
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return [CookbookFieldError(field="source", code="unsafe_url", message="Source URL must be a public HTTP(S) URL without credentials.")]
    return []


def _normalise_ingredient(item: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        "name": _normalise_text(str(item.get("name", ""))) or "",
        "quantity": _normalise_text(item.get("quantity")),
        "unit": _normalise_text(item.get("unit")),
        "note": _normalise_text(item.get("note")),
    }


def _normalise_instruction(item: Mapping[str, Any]) -> dict[str, Any]:
    return {"step": item.get("step"), "text": _normalise_text(str(item.get("text", ""))) or ""}


def _draft_mapping_errors(raw: Mapping[str, Any]) -> list[CookbookFieldError]:
    errors = _unknown_fields(raw, _DRAFT_FIELDS, "draft")
    ingredients = raw.get("ingredients")
    if isinstance(ingredients, list):
        for index, item in enumerate(ingredients):
            if isinstance(item, Mapping):
                errors.extend(_unknown_fields(item, _INGREDIENT_FIELDS, f"ingredients[{index}]"))
    instructions = raw.get("instructions")
    if isinstance(instructions, list):
        for index, item in enumerate(instructions):
            if isinstance(item, Mapping):
                errors.extend(_unknown_fields(item, _INSTRUCTION_FIELDS, f"instructions[{index}]"))
    return errors


def _candidate_idempotency_key(raw: Mapping[str, Any], supplied: str | None) -> str:
    if supplied and supplied.strip():
        return supplied.strip()[:200]
    return f"draft-{_safe_digest(raw)}"


def _build_candidate(raw: Mapping[str, Any], idempotency_key: str) -> tuple[CookbookImportCandidate | None, list[CookbookFieldError], list[str]]:
    errors = _draft_mapping_errors(raw)
    warnings: list[str] = []
    if errors:
        return None, errors, warnings

    try:
        draft = RecipeImportDraft.model_validate(raw)
    except ValidationError as exc:
        return None, _validation_errors(exc), warnings

    if len(draft.title) > MAX_TITLE_LENGTH:
        errors.append(CookbookFieldError(field="title", code="too_long", message=f"Title must be {MAX_TITLE_LENGTH} characters or fewer."))
    if draft.description and len(draft.description) > MAX_DESCRIPTION_LENGTH:
        errors.append(CookbookFieldError(field="description", code="too_long", message=f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."))
    if draft.notes and len(draft.notes) > MAX_NOTES_LENGTH:
        errors.append(CookbookFieldError(field="notes", code="too_long", message=f"Notes must be {MAX_NOTES_LENGTH} characters or fewer."))
    if draft.source and len(draft.source) > MAX_SOURCE_LENGTH:
        errors.append(CookbookFieldError(field="source", code="too_long", message=f"Source must be {MAX_SOURCE_LENGTH} characters or fewer."))
    if len(draft.ingredients) > MAX_INGREDIENTS:
        errors.append(CookbookFieldError(field="ingredients", code="too_many", message=f"At most {MAX_INGREDIENTS} ingredients are supported."))
    if len(draft.instructions) > MAX_INSTRUCTIONS:
        errors.append(CookbookFieldError(field="instructions", code="too_many", message=f"At most {MAX_INSTRUCTIONS} instructions are supported."))
    if any(len(value) > MAX_FIELD_LENGTH for item in draft.ingredients for value in (item.name, item.quantity, item.unit, item.note) if value):
        warnings.append("One or more ingredient fields are unusually long and require user review.")
    if any(len(item.text) > MAX_FIELD_LENGTH for item in draft.instructions):
        warnings.append("One or more instruction fields are unusually long and require user review.")
    if len(draft.tags) > MAX_TAGS or any(len(tag) > MAX_TAG_LENGTH for tag in draft.tags):
        errors.append(CookbookFieldError(field="tags", code="bounded_list", message="Tags exceed the candidate contract limits."))
    errors.extend(_source_errors(draft.source))

    steps = [item.step for item in draft.instructions]
    if steps != list(range(1, len(steps) + 1)):
        errors.append(CookbookFieldError(field="instructions.step", code="non_contiguous", message="Instruction steps must start at 1 and be contiguous."))
    if errors:
        return None, errors, warnings

    payload = CookbookRecipePayload(
        title=_normalise_text(draft.title) or "",
        description=_normalise_text(draft.description),
        servings=draft.servings,
        ingredients=[CookbookIngredientPayload(**_normalise_ingredient(item.model_dump())) for item in draft.ingredients],
        instructions=[CookbookInstructionPayload(**_normalise_instruction(item.model_dump())) for item in draft.instructions],
        tags=list(dict.fromkeys(_normalise_tag(tag) for tag in draft.tags if _normalise_tag(tag))),
        source=_normalise_text(draft.source),
        notes=_normalise_text(draft.notes),
    )
    ingredient_fingerprint = _safe_digest({"title": payload.title.lower(), "ingredients": sorted(item.name.lower() for item in payload.ingredients)})
    candidate_digest = _safe_digest({"key": idempotency_key, "fingerprint": ingredient_fingerprint})
    candidate = CookbookImportCandidate(
        candidate_id=f"candidate-{candidate_digest}",
        idempotency_key=idempotency_key,
        contract_version=CONTRACT_VERSION,
        schema_version=RECIPE_SCHEMA_VERSION,
        ingredient_fingerprint=ingredient_fingerprint,
        payload=payload,
    )
    return candidate, [], warnings


def map_import_draft_to_candidate(
    draft: RecipeImportDraft | Mapping[str, Any],
    *,
    idempotency_key: str | None = None,
    contract_version: str = CONTRACT_VERSION,
    schema_version: str = RECIPE_SCHEMA_VERSION,
) -> CookbookImportDryRunResult:
    """Map a draft in memory and return a safe result without side effects."""

    key = _candidate_idempotency_key(draft.model_dump() if isinstance(draft, RecipeImportDraft) else draft, idempotency_key)
    result_digest = _safe_digest({"key": key, "contract": contract_version, "schema": schema_version})
    result_id = f"dry-run-{result_digest}"
    metadata = CookbookIdempotencyMetadata(key=key, result_id=result_id)
    if contract_version != CONTRACT_VERSION or schema_version != RECIPE_SCHEMA_VERSION:
        return CookbookImportDryRunResult(
            status="schema_mismatch",
            contract_version=contract_version,
            schema_version=schema_version,
            errors=[CookbookFieldError(field="version", code="schema_mismatch", message="Candidate contract or schema version is unsupported.")],
            idempotency=metadata,
        )
    raw = draft.model_dump() if isinstance(draft, RecipeImportDraft) else dict(draft)
    if not isinstance(raw, Mapping):
        return CookbookImportDryRunResult(
            status="invalid",
            contract_version=contract_version,
            schema_version=schema_version,
            errors=[CookbookFieldError(field="draft", code="invalid_type", message="Draft must be an importer draft object." )],
            idempotency=metadata,
        )
    candidate, errors, warnings = _build_candidate(raw, key)
    return CookbookImportDryRunResult(
        status="valid" if candidate and not errors else "invalid",
        contract_version=contract_version,
        schema_version=schema_version,
        candidate=candidate,
        errors=errors,
        warnings=warnings,
        idempotency=metadata,
    )


class FakeCookbookAdapter:
    """In-memory fake core adapter; it has no persistence or network client."""

    def __init__(self, existing_recipes: Iterable[FakeCookbookRecipe | Mapping[str, Any]] = ()) -> None:
        self._existing = [recipe if isinstance(recipe, FakeCookbookRecipe) else FakeCookbookRecipe.model_validate(recipe) for recipe in existing_recipes]
        self._results: dict[str, tuple[str, CookbookImportDryRunResult]] = {}

    def dry_run_import_candidate(
        self,
        draft: RecipeImportDraft | Mapping[str, Any],
        *,
        idempotency_key: str | None = None,
        contract_version: str = CONTRACT_VERSION,
        schema_version: str = RECIPE_SCHEMA_VERSION,
    ) -> CookbookImportDryRunResult:
        raw = draft.model_dump() if isinstance(draft, RecipeImportDraft) else dict(draft)
        key = _candidate_idempotency_key(raw, idempotency_key)
        digest = _safe_digest({"draft": raw, "contract": contract_version, "schema": schema_version})
        cached = self._results.get(key)
        if cached:
            cached_digest, cached_result = cached
            if cached_digest != digest:
                return CookbookImportDryRunResult(
                    status="invalid",
                    contract_version=contract_version,
                    schema_version=schema_version,
                    errors=[CookbookFieldError(field="idempotency_key", code="key_reuse_conflict", message="Idempotency key was already used for a different candidate.")],
                    idempotency=CookbookIdempotencyMetadata(key=key, result_id=cached_result.idempotency.result_id, replayed=False),
                )
            return cached_result.model_copy(
                update={
                    "status": "idempotent_replay",
                    "idempotency": cached_result.idempotency.model_copy(update={"replayed": True}),
                }
            )

        result = map_import_draft_to_candidate(
            draft,
            idempotency_key=key,
            contract_version=contract_version,
            schema_version=schema_version,
        )
        if result.candidate:
            matches = []
            title = result.candidate.payload.title.casefold()
            names = {item.name.casefold() for item in result.candidate.payload.ingredients}
            for recipe in self._existing:
                existing_names = {name.strip().casefold() for name in recipe.ingredients if name.strip()}
                if recipe.title.strip().casefold() == title and existing_names == names:
                    matches.append(CookbookDuplicateCandidate(recipe_id=recipe.recipe_id, title=recipe.title, match="title_and_ingredients"))
            result = result.model_copy(
                update={
                    "status": "duplicate" if matches else result.status,
                    "duplicate_candidates": matches,
                    "warnings": [*result.warnings, "A possible duplicate exists; review it before any future save."] if matches else result.warnings,
                }
            )
        self._results[key] = (digest, result)
        return result
