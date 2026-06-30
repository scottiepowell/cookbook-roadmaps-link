import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderAvailability:
    configured: bool


PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "ollama": "OLLAMA_BASE_URL",
}

DEFAULT_COOKBOOK_DB_PATH = "/data/cookbook-db/dev.db"


def _is_configured(value: str | None) -> bool:
    return bool(value and value.strip())


def get_provider_config() -> dict[str, ProviderAvailability]:
    return {
        provider: ProviderAvailability(configured=_is_configured(os.getenv(env_name)))
        for provider, env_name in PROVIDER_ENV_VARS.items()
    }


def get_cookbook_db_path() -> str:
    return os.getenv("COOKBOOK_DB_PATH", DEFAULT_COOKBOOK_DB_PATH)
