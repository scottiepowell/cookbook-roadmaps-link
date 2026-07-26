"""Disabled-by-default local commit service for reviewed Cookbook candidates.

This is an internal local adapter boundary, not an HTTP route or production
integration.  The default store is in-memory so normal tests cannot touch
SQLite, uploads, the upstream app, or a provider.  A future local runtime
caller may inject a disposable store only after its own backup and restore
guards have passed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.cookbook_import_adapter import (
    CONTRACT_VERSION,
    RECIPE_SCHEMA_VERSION,
    CookbookFieldError,
    CookbookImportCandidate,
    CookbookImportDryRunResult,
    FakeCookbookAdapter,
    map_import_draft_to_candidate,
)
from app.schemas import RecipeImportDraft


class LocalCommitResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["import_candidate_commit"] = "import_candidate_commit"
    status: Literal["committed", "duplicate", "idempotent_replay", "conflict", "invalid", "unavailable"]
    contract_version: str
    schema_version: str
    local_recipe_id: str | None = None
    idempotency_key: str | None = None
    errors: list[CookbookFieldError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LocalCommitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft: dict[str, Any]
    idempotency_key: str | None = None
    confirm_local_save: bool = False


class LocalCommitGuard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    approved: bool = False
    runtime_verified: bool = False
    compose_project: str = "cookbook-local"
    target_url: str = "http://127.0.0.1:3000/"
    synthetic_owner: bool = True


class InMemoryLocalCookbookStore:
    """Small deterministic store used by tests and local service callers."""

    def __init__(self, *, failure_after_insert: bool = False) -> None:
        self.recipes: dict[str, dict[str, Any]] = {}
        self.idempotency: dict[str, tuple[str, str]] = {}
        self.failure_after_insert = failure_after_insert

    @staticmethod
    def _fingerprint(candidate: CookbookImportCandidate, owner_id: str) -> str:
        material = {
            "owner": owner_id,
            "title": candidate.payload.title.casefold(),
            "ingredients": sorted(item.name.casefold() for item in candidate.payload.ingredients),
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]

    def find_duplicate(self, candidate: CookbookImportCandidate, owner_id: str) -> str | None:
        fingerprint = self._fingerprint(candidate, owner_id)
        for recipe_id, recipe in self.recipes.items():
            if recipe["owner_id"] == owner_id and recipe["fingerprint"] == fingerprint:
                return recipe_id
        return None

    def commit(self, candidate: CookbookImportCandidate, owner_id: str, serialized_payload: dict[str, Any]) -> tuple[str, str]:
        previous = dict(self.recipes)
        recipe_id = str(uuid4())
        fingerprint = self._fingerprint(candidate, owner_id)
        self.recipes[recipe_id] = {
            "owner_id": owner_id,
            "fingerprint": fingerprint,
            "candidate_id": candidate.candidate_id,
            "payload": serialized_payload,
        }
        if self.failure_after_insert:
            self.recipes = previous
            raise RuntimeError("local transaction failed")
        self.idempotency[candidate.idempotency_key] = (candidate.candidate_id, recipe_id)
        return recipe_id, fingerprint


def _guard_error(field: str, code: str, message: str) -> CookbookFieldError:
    return CookbookFieldError(field=field, code=code, message=message)


def validate_local_commit_guard(guard: LocalCommitGuard) -> list[CookbookFieldError]:
    errors: list[CookbookFieldError] = []
    if not guard.enabled or not guard.approved:
        errors.append(_guard_error("operation", "disabled", "Local Cookbook commit is disabled without explicit approval."))
    if not guard.runtime_verified:
        errors.append(_guard_error("runtime", "unverified", "The disposable cookbook-local runtime must be verified before commit."))
    if guard.compose_project != "cookbook-local":
        errors.append(_guard_error("compose_project", "not_local", "Only the cookbook-local Compose project is accepted."))
    if not guard.synthetic_owner:
        errors.append(_guard_error("owner", "synthetic_only", "Only synthetic local ownership is accepted."))
    lowered = guard.target_url.casefold()
    if re.search(r"cookbook\.roadmaps\.link|cloudflare|tunnel|aws|github|production|deploy", lowered):
        errors.append(_guard_error("target_url", "non_local_target", "Only the disposable loopback Cookbook target is accepted."))
    try:
        parsed = urlparse(guard.target_url)
    except ValueError:
        parsed = None
    try:
        port = parsed.port if parsed is not None else None
    except ValueError:
        port = -1
    if parsed is None or parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or port not in {3000, None}:
        errors.append(_guard_error("target_url", "non_loopback", "Cookbook commit requires loopback HTTP on the local target."))
    return errors


def _candidate_payload(candidate: CookbookImportCandidate) -> dict[str, Any]:
    """Serialize only the schema-informed first-write fields."""

    source = candidate.payload.source
    source_url = source if source and urlparse(source).scheme in {"http", "https"} else None
    return {
        "name": candidate.payload.title,
        "description": candidate.payload.description,
        "servings": str(candidate.payload.servings) if candidate.payload.servings is not None else None,
        "ingredients": "\n".join(
            " ".join(part for part in (item.quantity, item.unit, item.name) if part) + (f" ({item.note})" if item.note else "")
            for item in candidate.payload.ingredients
        ),
        "directions": "\n".join(f"{item.step}. {item.text}" for item in candidate.payload.instructions),
        "source": None if source_url else source,
        "source_url": source_url,
        "notes": candidate.payload.notes,
        "categories": None,
        "media": None,
        "embeddings": None,
    }


class LocalCookbookCommitService:
    """Commit reviewed candidates to an injected local-only store."""

    def __init__(self, *, store: InMemoryLocalCookbookStore | None = None, owner_id: str = "synthetic-local-owner") -> None:
        self.store = store or InMemoryLocalCookbookStore()
        self.owner_id = owner_id

    def commit(
        self,
        draft: RecipeImportDraft | Mapping[str, Any],
        *,
        guard: LocalCommitGuard | None = None,
        idempotency_key: str | None = None,
        contract_version: str = CONTRACT_VERSION,
        schema_version: str = RECIPE_SCHEMA_VERSION,
    ) -> LocalCommitResult:
        effective_guard = guard or LocalCommitGuard()
        guard_errors = validate_local_commit_guard(effective_guard)
        if guard_errors:
            return LocalCommitResult(status="unavailable", contract_version=contract_version, schema_version=schema_version, errors=guard_errors)

        dry_run = map_import_draft_to_candidate(
            draft,
            idempotency_key=idempotency_key,
            contract_version=contract_version,
            schema_version=schema_version,
        )
        if dry_run.candidate is None:
            return LocalCommitResult(
                status="invalid",
                contract_version=contract_version,
                schema_version=schema_version,
                idempotency_key=dry_run.idempotency.key,
                errors=dry_run.errors,
                warnings=dry_run.warnings,
            )

        candidate = dry_run.candidate
        prior = self.store.idempotency.get(candidate.idempotency_key)
        if prior:
            if prior[0] == candidate.candidate_id:
                return LocalCommitResult(status="idempotent_replay", contract_version=contract_version, schema_version=schema_version, local_recipe_id=prior[1], idempotency_key=candidate.idempotency_key)
            return LocalCommitResult(status="conflict", contract_version=contract_version, schema_version=schema_version, idempotency_key=candidate.idempotency_key, errors=[_guard_error("idempotency_key", "key_reuse_conflict", "Idempotency key was already used for a different candidate.")])

        duplicate_id = self.store.find_duplicate(candidate, self.owner_id)
        if duplicate_id:
            return LocalCommitResult(status="duplicate", contract_version=contract_version, schema_version=schema_version, local_recipe_id=duplicate_id, idempotency_key=candidate.idempotency_key, warnings=["A matching local recipe exists; no second write was performed."])

        try:
            local_recipe_id, _ = self.store.commit(candidate, self.owner_id, _candidate_payload(candidate))
        except RuntimeError:
            return LocalCommitResult(status="unavailable", contract_version=contract_version, schema_version=schema_version, idempotency_key=candidate.idempotency_key, errors=[_guard_error("storage", "local_transaction_failed", "The local transaction failed and was rolled back safely.")])
        return LocalCommitResult(status="committed", contract_version=contract_version, schema_version=schema_version, local_recipe_id=local_recipe_id, idempotency_key=candidate.idempotency_key, warnings=["Local-only commit; categories, media, and embeddings were excluded."])


__all__ = ["InMemoryLocalCookbookStore", "LocalCommitGuard", "LocalCommitResult", "LocalCookbookCommitService", "validate_local_commit_guard"]
