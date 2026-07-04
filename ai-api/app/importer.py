from pydantic import ValidationError

from app.config import get_ai_settings
from app.providers import LLMProvider, StructuredLLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.schemas import RecipeImportDraft, RecipeImportRequest, RecipeImportResponse


IMPORTER_SYSTEM_PROMPT = (
    "Extract a recipe draft from pasted user text. Return only fields that fit the provided schema. "
    "Do not invent database IDs, do not write to any database, and keep uncertain details in notes."
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
        warnings=[],
        usage=provider_response.usage,
    )


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise RecipeImportProviderError("Recipe importer provider is not configured.") from exc


def _build_prompt(request: RecipeImportRequest) -> str:
    source_line = f"Source: {request.source.strip()}\n" if request.source and request.source.strip() else ""
    return f"{source_line}Recipe text:\n{request.text.strip()}"
