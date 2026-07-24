import os
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit


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


@dataclass(frozen=True)
class OperatorGateSettings:
    enabled: bool
    token_fingerprint: str
    allowed_workflows: tuple[str, ...]
    local_bypass: bool


@dataclass(frozen=True)
class ProviderBudgetSettings:
    calls_enabled: bool
    global_disable: bool
    max_calls_per_demo_session: int
    max_input_tokens_per_call: int
    max_output_tokens_per_call: int
    max_total_tokens_per_call: int
    max_estimated_cost_usd_per_session: Decimal
    max_estimated_cost_usd_per_call: Decimal
    budget_mode: str
    configured: bool
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class InviteSessionSettings:
    enabled: bool
    session_ttl_seconds: int
    grant_ttl_seconds: int
    max_sessions_per_grant: int
    default_max_provider_calls: int
    default_max_estimated_cost_usd: Decimal
    allowed_workflows: tuple[str, ...]
    local_operator_create_enabled: bool
    configured: bool
    validation_errors: tuple[str, ...]


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
DEFAULT_AI_OPERATOR_GATE_ENABLED = False
DEFAULT_AI_OPERATOR_GATE_ALLOWED_WORKFLOWS = ("importer", "dataset_ask", "recipe_session", "meal_plan")
DEFAULT_AI_OPERATOR_GATE_LOCAL_BYPASS = True
DEFAULT_AI_PROVIDER_CALLS_ENABLED = True
DEFAULT_AI_PROVIDER_GLOBAL_DISABLE = False
DEFAULT_AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION = 10
DEFAULT_AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL = 12000
DEFAULT_AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL = 1200
DEFAULT_AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL = 14000
DEFAULT_AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION = Decimal("1.00")
DEFAULT_AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL = Decimal("0.25")
DEFAULT_AI_PROVIDER_BUDGET_MODE = "enforce"
DEFAULT_AI_INVITE_SESSIONS_ENABLED = False
DEFAULT_AI_INVITE_SESSION_TTL_SECONDS = 1800
DEFAULT_AI_INVITE_GRANT_TTL_SECONDS = 3600
DEFAULT_AI_INVITE_MAX_SESSIONS_PER_GRANT = 1
DEFAULT_AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS = 5
DEFAULT_AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD = Decimal("0.50")
DEFAULT_AI_INVITE_ALLOWED_WORKFLOWS = ("importer", "dataset_ask", "recipe_session", "meal_plan")
DEFAULT_AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED = True

PROVIDER_ENV_VARS = {
    "mock": None,
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "ollama": "OLLAMA_BASE_URL",
}

DEFAULT_COOKBOOK_DB_PATH = "/data/cookbook-db/dev.db"
DEFAULT_COOKBOOK_TARGET_URL = "http://127.0.0.1:3000/"


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


def get_cookbook_target_url() -> str:
    """Return a safe external Cookbook handoff target.

    The target is an operator/deployment URL, not a secret. Invalid values
    fail closed to the local Compose target and are never echoed to clients.
    """
    raw_value = os.getenv("COOKBOOK_TARGET_URL", "").strip()
    if not raw_value:
        return DEFAULT_COOKBOOK_TARGET_URL

    try:
        parsed = urlsplit(raw_value)
    except ValueError:
        return DEFAULT_COOKBOOK_TARGET_URL

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return DEFAULT_COOKBOOK_TARGET_URL

    path = parsed.path or "/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


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


def get_operator_gate_settings() -> OperatorGateSettings:
    token_fingerprint = _normalize_fingerprint(os.getenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT"))
    raw_token = os.getenv("AI_OPERATOR_GATE_TOKEN")
    if not token_fingerprint and raw_token and raw_token.strip():
        token_fingerprint = _fingerprint_token(raw_token.strip())
    allowed_workflows = _parse_csv_env(
        "AI_OPERATOR_GATE_ALLOWED_WORKFLOWS",
        DEFAULT_AI_OPERATOR_GATE_ALLOWED_WORKFLOWS,
    )
    return OperatorGateSettings(
        enabled=_bool_env("AI_OPERATOR_GATE_ENABLED", default=DEFAULT_AI_OPERATOR_GATE_ENABLED),
        token_fingerprint=token_fingerprint,
        allowed_workflows=tuple(allowed_workflows),
        local_bypass=_bool_env("AI_OPERATOR_GATE_LOCAL_BYPASS", default=DEFAULT_AI_OPERATOR_GATE_LOCAL_BYPASS),
    )


def get_provider_budget_settings() -> ProviderBudgetSettings:
    errors: list[str] = []
    calls_enabled = _strict_bool_env(
        "AI_PROVIDER_CALLS_ENABLED",
        DEFAULT_AI_PROVIDER_CALLS_ENABLED,
        errors=errors,
    )
    global_disable = _strict_bool_env(
        "AI_PROVIDER_GLOBAL_DISABLE",
        DEFAULT_AI_PROVIDER_GLOBAL_DISABLE,
        errors=errors,
    )
    max_calls = _strict_int_env(
        "AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION",
        DEFAULT_AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION,
        minimum=1,
        errors=errors,
    )
    max_input_tokens = _strict_int_env(
        "AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL",
        DEFAULT_AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL,
        minimum=1,
        errors=errors,
    )
    max_output_tokens = _strict_int_env(
        "AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL",
        DEFAULT_AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL,
        minimum=1,
        errors=errors,
    )
    max_total_tokens = _strict_int_env(
        "AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL",
        DEFAULT_AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL,
        minimum=1,
        errors=errors,
    )
    max_session_cost = _strict_decimal_env(
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION",
        DEFAULT_AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION,
        minimum=Decimal("0.00"),
        errors=errors,
    )
    max_call_cost = _strict_decimal_env(
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL",
        DEFAULT_AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL,
        minimum=Decimal("0.00"),
        errors=errors,
    )
    budget_mode = os.getenv("AI_PROVIDER_BUDGET_MODE", DEFAULT_AI_PROVIDER_BUDGET_MODE).strip().lower()
    if not budget_mode:
        budget_mode = DEFAULT_AI_PROVIDER_BUDGET_MODE
    if budget_mode not in {"enforce", "warn"}:
        errors.append("AI_PROVIDER_BUDGET_MODE must be 'enforce' or 'warn'.")
        budget_mode = DEFAULT_AI_PROVIDER_BUDGET_MODE

    return ProviderBudgetSettings(
        calls_enabled=calls_enabled,
        global_disable=global_disable,
        max_calls_per_demo_session=max_calls,
        max_input_tokens_per_call=max_input_tokens,
        max_output_tokens_per_call=max_output_tokens,
        max_total_tokens_per_call=max_total_tokens,
        max_estimated_cost_usd_per_session=max_session_cost,
        max_estimated_cost_usd_per_call=max_call_cost,
        budget_mode=budget_mode,
        configured=not errors,
        validation_errors=tuple(errors),
    )


def get_invite_session_settings() -> InviteSessionSettings:
    errors: list[str] = []
    session_ttl_seconds = _strict_int_env(
        "AI_INVITE_SESSION_TTL_SECONDS",
        DEFAULT_AI_INVITE_SESSION_TTL_SECONDS,
        minimum=1,
        errors=errors,
    )
    grant_ttl_seconds = _strict_int_env(
        "AI_INVITE_GRANT_TTL_SECONDS",
        DEFAULT_AI_INVITE_GRANT_TTL_SECONDS,
        minimum=1,
        errors=errors,
    )
    max_sessions_per_grant = _strict_int_env(
        "AI_INVITE_MAX_SESSIONS_PER_GRANT",
        DEFAULT_AI_INVITE_MAX_SESSIONS_PER_GRANT,
        minimum=1,
        errors=errors,
    )
    default_max_provider_calls = _strict_int_env(
        "AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS",
        DEFAULT_AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS,
        minimum=0,
        errors=errors,
    )
    default_max_estimated_cost_usd = _strict_decimal_env(
        "AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD",
        DEFAULT_AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD,
        minimum=Decimal("0.00"),
        errors=errors,
    )
    allowed_workflows = _parse_csv_env(
        "AI_INVITE_ALLOWED_WORKFLOWS",
        DEFAULT_AI_INVITE_ALLOWED_WORKFLOWS,
    )
    return InviteSessionSettings(
        enabled=_bool_env("AI_INVITE_SESSIONS_ENABLED", default=DEFAULT_AI_INVITE_SESSIONS_ENABLED),
        session_ttl_seconds=session_ttl_seconds,
        grant_ttl_seconds=grant_ttl_seconds,
        max_sessions_per_grant=max_sessions_per_grant,
        default_max_provider_calls=default_max_provider_calls,
        default_max_estimated_cost_usd=default_max_estimated_cost_usd,
        allowed_workflows=tuple(allowed_workflows),
        local_operator_create_enabled=_bool_env(
            "AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED",
            default=DEFAULT_AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED,
        ),
        configured=not errors,
        validation_errors=tuple(errors),
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


def _strict_bool_env(name: str, default: bool, *, errors: list[str]) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    errors.append(f"{name} must be a boolean value.")
    return default


def _strict_int_env(name: str, default: int, *, minimum: int, errors: list[str]) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = int(raw_value)
    except ValueError:
        errors.append(f"{name} must be an integer.")
        return default
    if value < minimum:
        errors.append(f"{name} must be greater than or equal to {minimum}.")
        return default
    return value


def _strict_decimal_env(name: str, default: Decimal, *, minimum: Decimal, errors: list[str]) -> Decimal:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = Decimal(raw_value.strip())
    except Exception:
        errors.append(f"{name} must be a decimal value.")
        return default
    if value < minimum:
        errors.append(f"{name} must be greater than or equal to {minimum}.")
        return default
    return value


def _parse_csv_env(name: str, default: tuple[str, ...]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return list(default)
    values: list[str] = []
    for piece in raw_value.split(","):
        value = piece.strip().lower()
        if value and value not in values:
            values.append(value)
    return values or list(default)


def _normalize_fingerprint(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def _fingerprint_token(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
