"""Internal, no-write dry-run operation for Cookbook import candidates.

The operation is intentionally a service boundary rather than an HTTP route.
Callers must explicitly enable it in local/internal code.  It delegates all
mapping and validation to the fixture-only adapter and has no database,
filesystem, network, provider, or authentication dependency.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.cookbook_import_adapter import (
    CONTRACT_VERSION,
    RECIPE_SCHEMA_VERSION,
    CookbookFieldError,
    CookbookImportDryRunResult,
    FakeCookbookAdapter,
)
from app.schemas import RecipeImportDraft


class CookbookImportDryRunOperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["import_candidate_dry_run"] = "import_candidate_dry_run"
    status: Literal["ready", "unavailable"]
    contract_version: str
    schema_version: str
    result: CookbookImportDryRunResult | None = None
    errors: list[CookbookFieldError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def dry_run_import_candidate_operation(
    draft: RecipeImportDraft | Mapping[str, Any],
    *,
    enabled: bool = False,
    adapter: FakeCookbookAdapter | None = None,
    idempotency_key: str | None = None,
    contract_version: str = CONTRACT_VERSION,
    schema_version: str = RECIPE_SCHEMA_VERSION,
) -> CookbookImportDryRunOperationResponse:
    """Run a local/internal candidate dry run, never a save operation.

    ``enabled`` is an explicit non-secret internal gate.  It defaults to false
    so a future caller must consciously opt into the local operation.  The
    function never opens or creates storage and never contacts a provider.
    """

    if not enabled:
        return CookbookImportDryRunOperationResponse(
            status="unavailable",
            contract_version=contract_version,
            schema_version=schema_version,
            errors=[CookbookFieldError(field="operation", code="disabled", message="Local import-candidate dry run is disabled.")],
        )

    result = (adapter or FakeCookbookAdapter()).dry_run_import_candidate(
        draft,
        idempotency_key=idempotency_key,
        contract_version=contract_version,
        schema_version=schema_version,
    )
    return CookbookImportDryRunOperationResponse(
        status="ready",
        contract_version=contract_version,
        schema_version=schema_version,
        result=result,
        errors=result.errors,
        warnings=result.warnings,
    )
