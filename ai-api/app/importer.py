from pydantic import ValidationError

from app.config import get_ai_settings
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_recipe_import_input
from app.providers import LLMProvider, StructuredLLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.schemas import RecipeImportDraft, RecipeImportRequest, RecipeImportResponse


IMPORTER_SYSTEM_PROMPT = (
    "Extract a recipe draft from pasted user text. Return only fields that fit the provided schema. "
    "Use a one-sentence description with one or two core ingredients when possible. "
    "Keep missing quantities, timing, or unspecified details in notes. "
    "Do not invent unrelated ingredients, do not invent database IDs, and do not write to any database."
)


class RecipeImporterError(RuntimeError):
    """Base error for recipe importer failures."""


class RecipeImportValidationError(RecipeImporterError):
    """Raised when provider output cannot be validated as a recipe draft."""


class RecipeImportProviderError(RecipeImporterError):
    """Raised when the configured provider cannot produce an importer draft."""


def import_recipe_text(
    request: RecipeImportRequest,
    provider: LLMProvider | None = None,
) -> RecipeImportResponse:
    input_quality = classify_recipe_import_input(request.text)
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return RecipeImportResponse(
            draft=None,
            provider="none",
            model="none",
            warnings=input_quality.warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    active_provider = provider or _get_configured_provider()
    schema = RecipeImportDraft.model_json_schema()
    try:
        provider_response = active_provider.generate_structured(
            StructuredLLMRequest(
                prompt=_build_prompt(request),
                system=IMPORTER_SYSTEM_PROMPT,
                schema_name="RecipeImportDraft",
                schema=schema,
                max_output_tokens=get_ai_settings().max_output_tokens,
            )
        )
    except ProviderError as exc:
        raise RecipeImportProviderError("Recipe importer provider failed.") from exc

    try:
        draft = RecipeImportDraft.model_validate(provider_response.data)
    except ValidationError as exc:
        raise RecipeImportValidationError("Provider returned an invalid recipe draft.") from exc

    return RecipeImportResponse(
        draft=draft,
        provider=provider_response.provider,
        model=provider_response.model,
        warnings=input_quality.warnings if input_quality.status == WEAK_BUT_USABLE else [],
        usage=provider_response.usage,
        input_quality=input_quality.to_dict(),
    )


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise RecipeImportProviderError("Recipe importer provider is not configured.") from exc


def _build_prompt(request: RecipeImportRequest) -> str:
    source_line = f"Source: {request.source.strip()}\n" if request.source and request.source.strip() else ""
    return f"{source_line}Recipe text:\n{request.text.strip()}"
