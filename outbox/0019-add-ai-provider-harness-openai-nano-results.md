# Task 0019 Results: Add AI Provider Harness With OpenAI Nano

## Summary

Added the AI provider harness for the `ai-api` sidecar. The default provider is deterministic `mock`, and the first real provider path is OpenAI. The OpenAI path defaults to `gpt-5.4-nano` and records `gpt-5.4-mini` as the configured fallback.

This task did not add recipe importing, RAG, meal planning, embeddings, cookbook DB write-back, or live AI provider calls.

## Files Created

- `ai-api/app/providers/__init__.py`
- `ai-api/app/providers/base.py`
- `ai-api/app/providers/errors.py`
- `ai-api/app/providers/mock.py`
- `ai-api/app/providers/openai_provider.py`
- `ai-api/app/providers/registry.py`
- `ai-api/tests/test_providers.py`
- `outbox/0019-add-ai-provider-harness-openai-nano-results.md`

## Files Modified

- `.env.example`
- `ai-api/README.md`
- `ai-api/app/config.py`
- `ai-api/requirements.txt`
- `ai-api/tests/test_config.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md`
- `docs/repo-map.md`

## Provider Interface Summary

The provider interface defines:

- `LLMRequest`
- `LLMResponse`
- `StructuredLLMRequest`
- `StructuredLLMResponse`
- `LLMProvider`

The registry exposes `get_provider()`, selecting:

- `mock` -> `MockProvider`
- `openai` -> `OpenAIProvider`
- unsupported values -> controlled `ProviderConfigError`

## Mock Provider Behavior

The mock provider:

- is selected by default when `AI_PROVIDER` is unset or `mock`;
- makes no network calls;
- returns deterministic text responses;
- returns deterministic schema-shaped structured responses for later importer, RAG, and meal-plan tests;
- is used by all automated tests.

## OpenAI Provider Readiness And Limitations

The OpenAI provider:

- uses the official OpenAI Python SDK lazily;
- makes no calls at import or construction time;
- fails clearly if selected without `OPENAI_API_KEY`;
- defaults to `gpt-5.4-nano`;
- records `gpt-5.4-mini` as `OPENAI_FALLBACK_MODEL`;
- supports text and structured JSON generation through the provider interface;
- applies `AI_TIMEOUT_SECONDS` and `AI_MAX_OUTPUT_TOKENS`.

No live OpenAI call was run. A manual smoke test remains opt-in documentation only.

## Cost-Control Defaults

`.env.example` now records:

```text
AI_PROVIDER=mock
AI_MODEL=mock-basic
AI_MAX_OUTPUT_TOKENS=700
AI_TIMEOUT_SECONDS=20
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
OPENAI_ENABLE_LIVE_TESTS=false
```

Docs also record these controls:

- use deterministic search before future model calls;
- keep prompts small;
- cap output tokens;
- keep automated tests mock-only;
- make OpenAI live smoke tests explicit and manual.

## Validation Commands And Results

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `pytest ai-api/tests`: could not run directly because `pytest` is not installed on the shell PATH.
- `bash -n scripts/validate-repo.sh`: passed using Git Bash.
- `bash scripts/validate-repo.sh`: passed.
  - Docker Compose configuration: PASS
  - AI API tests: PASS, `26 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Recommended Next Task

Proceed with task 0020: add the structured recipe importer using the mock provider for automated tests and OpenAI only for explicit manual smoke testing.
