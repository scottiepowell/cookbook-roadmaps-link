import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderAvailability:
    configured: bool


@dataclass(frozen=True)
class AISettings:
    provider: str
    model: str
    max_output_tokens: int
    timeout_seconds: float
    provider_debug: bool
    openai_model: str
    openai_fallback_model: str
    openai_live_tests_enabled: bool


@dataclass(frozen=True)
class RetrievalCacheSettings:
    enabled: bool
    max_entries: int
    ttl_seconds: int


DEFAULT_AI_PROVIDER = "mock"
DEFAULT_AI_MODEL = "mock-basic"
DEFAULT_AI_MAX_OUTPUT_TOKENS = 700
DEFAULT_AI_TIMEOUT_SECONDS = 20.0
DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"
DEFAULT_OPENAI_FALLBACK_MODEL = "gpt-5.4-mini"
DEFAULT_RECIPE_DATASET_DIR = "recipe-dataset"
DEFAULT_RECIPE_DATASET_INDEX_LIMIT = 100
DEFAULT_AI_RETRIEVAL_CACHE_ENABLED = True
DEFAULT_AI_RETRIEVAL_CACHE_MAX_ENTRIES = 128
DEFAULT_AI_RETRIEVAL_CACHE_TTL_SECONDS = 900

PROVIDER_ENV_VARS = {
    "mock": None,
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "ollama": "OLLAMA_BASE_URL",
}

DEFAULT_COOKBOOK_DB_PATH = "/data/cookbook-db/dev.db"


def _is_configured(value: str | None) -> bool:
    return bool(value and value.strip())


def get_provider_config() -> dict[str, ProviderAvailability]:
    providers: dict[str, ProviderAvailability] = {}
    for provider, env_name in PROVIDER_ENV_VARS.items():
        providers[provider] = ProviderAvailability(
            configured=True if env_name is None else _is_configured(os.getenv(env_name))
        )
    return providers


def get_cookbook_db_path() -> str:
    return os.getenv("COOKBOOK_DB_PATH", DEFAULT_COOKBOOK_DB_PATH)


def get_recipe_dataset_dir() -> str:
    return os.getenv("RECIPE_DATASET_DIR", DEFAULT_RECIPE_DATASET_DIR)


def get_recipe_dataset_index_limit() -> int:
    raw_value = os.getenv("RECIPE_DATASET_INDEX_LIMIT", str(DEFAULT_RECIPE_DATASET_INDEX_LIMIT))
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_RECIPE_DATASET_INDEX_LIMIT
    return max(1, min(value, 5000))


def get_ai_settings() -> AISettings:
    return AISettings(
        provider=os.getenv("AI_PROVIDER", DEFAULT_AI_PROVIDER).strip().lower() or DEFAULT_AI_PROVIDER,
        model=os.getenv("AI_MODEL", DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL,
        max_output_tokens=_int_env("AI_MAX_OUTPUT_TOKENS", DEFAULT_AI_MAX_OUTPUT_TOKENS),
        timeout_seconds=_float_env("AI_TIMEOUT_SECONDS", DEFAULT_AI_TIMEOUT_SECONDS),
        provider_debug=_bool_env("AI_PROVIDER_DEBUG", default=False),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL,
        openai_fallback_model=(
            os.getenv("OPENAI_FALLBACK_MODEL", DEFAULT_OPENAI_FALLBACK_MODEL).strip()
            or DEFAULT_OPENAI_FALLBACK_MODEL
        ),
        openai_live_tests_enabled=_bool_env("OPENAI_ENABLE_LIVE_TESTS", default=False),
    )


def get_retrieval_cache_settings() -> RetrievalCacheSettings:
    return RetrievalCacheSettings(
        enabled=_bool_env("AI_RETRIEVAL_CACHE_ENABLED", default=DEFAULT_AI_RETRIEVAL_CACHE_ENABLED),
        max_entries=max(1, _int_env("AI_RETRIEVAL_CACHE_MAX_ENTRIES", DEFAULT_AI_RETRIEVAL_CACHE_MAX_ENTRIES)),
        ttl_seconds=max(0, _int_env("AI_RETRIEVAL_CACHE_TTL_SECONDS", DEFAULT_AI_RETRIEVAL_CACHE_TTL_SECONDS)),
    )


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if not raw_value or not raw_value.strip():
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}
