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
    openai_model: str
    openai_fallback_model: str
    openai_live_tests_enabled: bool


DEFAULT_AI_PROVIDER = "mock"
DEFAULT_AI_MODEL = "mock-basic"
DEFAULT_AI_MAX_OUTPUT_TOKENS = 700
DEFAULT_AI_TIMEOUT_SECONDS = 20.0
DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"
DEFAULT_OPENAI_FALLBACK_MODEL = "gpt-5.4-mini"

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


def get_ai_settings() -> AISettings:
    return AISettings(
        provider=os.getenv("AI_PROVIDER", DEFAULT_AI_PROVIDER).strip().lower() or DEFAULT_AI_PROVIDER,
        model=os.getenv("AI_MODEL", DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL,
        max_output_tokens=_int_env("AI_MAX_OUTPUT_TOKENS", DEFAULT_AI_MAX_OUTPUT_TOKENS),
        timeout_seconds=_float_env("AI_TIMEOUT_SECONDS", DEFAULT_AI_TIMEOUT_SECONDS),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL,
        openai_fallback_model=(
            os.getenv("OPENAI_FALLBACK_MODEL", DEFAULT_OPENAI_FALLBACK_MODEL).strip()
            or DEFAULT_OPENAI_FALLBACK_MODEL
        ),
        openai_live_tests_enabled=_bool_env("OPENAI_ENABLE_LIVE_TESTS", default=False),
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
