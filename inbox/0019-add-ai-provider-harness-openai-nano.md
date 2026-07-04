# Task 0019: Add AI Provider Harness With Mock Default And OpenAI Nano

## Goal

Add the AI provider harness for the cookbook sidecar.

The default provider must be `mock` so local validation and CI stay offline and deterministic. The first real provider must be OpenAI, using a low-cost nano model by default for live/manual testing.

This task should not implement recipe importing, RAG, meal planning, embeddings, or write-back. It only creates the provider layer that later tasks will use.

## Current context

Completed foundations:

- 0016: FastAPI sidecar scaffold.
- 0017: read-only SQLite recipe reader.
- 0018: deterministic recipe search API.

Next tasks will use this provider harness:

- 0020: structured recipe importer.
- 0021: RAG ask endpoint.
- 0022: meal planner and shopping list.

## Provider strategy

Use this approach:

```text
Default provider: mock
First real provider: openai
Default OpenAI model: gpt-5.4-nano
Fallback OpenAI model: gpt-5.4-mini
```

Design for cheap customer usage:

- small prompts;
- deterministic search before LLM calls;
- low max output tokens;
- mock provider in all automated tests;
- optional manual live smoke test only.

## Configuration

Add/update environment config without secrets committed:

```text
AI_PROVIDER=mock
AI_MODEL=mock-basic
AI_MAX_OUTPUT_TOKENS=700
AI_TIMEOUT_SECONDS=20
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
OPENAI_ENABLE_LIVE_TESTS=false
```

Update `.env.example` with placeholders only.

`GET /ai/config` must keep reporting provider availability without exposing API keys, token fragments, raw base URLs, or secret values.

## Required implementation

### 1. Provider package

Add a provider package such as:

```text
ai-api/app/providers/
  __init__.py
  base.py
  errors.py
  mock.py
  openai_provider.py
  registry.py
```

Suggested abstractions:

```python
class LLMRequest(BaseModel):
    prompt: str
    system: str | None = None
    max_output_tokens: int | None = None
    temperature: float | None = None

class LLMResponse(BaseModel):
    text: str
    provider: str
    model: str
    usage: dict[str, int] | None = None

class StructuredLLMRequest(BaseModel):
    prompt: str
    schema_name: str
    schema: dict[str, Any]
    system: str | None = None
    max_output_tokens: int | None = None

class StructuredLLMResponse(BaseModel):
    data: dict[str, Any]
    provider: str
    model: str
    usage: dict[str, int] | None = None
```

Adjust names as needed, but keep the interface simple and testable.

### 2. Mock provider

Implement a deterministic mock provider.

Requirements:

- no network calls;
- deterministic text response;
- deterministic structured response that can echo or produce fixture-like JSON;
- useful for importer/RAG tests later;
- default provider selected when `AI_PROVIDER` is unset or `mock`.

### 3. OpenAI provider path

Add an OpenAI provider implementation that is ready for manual live use.

Requirements:

- use the official OpenAI Python SDK if needed;
- do not make live calls at import time;
- fail clearly if selected but `OPENAI_API_KEY` is missing;
- default to `gpt-5.4-nano`;
- support `OPENAI_FALLBACK_MODEL` config but do not auto-spend on fallback unless explicitly called by future code;
- support text generation and structured JSON generation through the same provider interface;
- apply timeout and max output token limits.

If the exact SDK call shape is uncertain, create the provider skeleton and tests around configuration/mock behavior, then document the manual live test as pending. Prefer a working minimal OpenAI call if it can be implemented safely without running it.

### 4. Provider registry

Add a registry/factory function such as:

```python
get_provider() -> LLMProvider
```

It should select providers from config:

- `mock` -> mock provider;
- `openai` -> OpenAI provider;
- unsupported value -> controlled config error.

### 5. Tests

Add offline tests only.

Cover:

- default provider is mock;
- mock text response is deterministic;
- mock structured response is deterministic and schema-shaped enough for later tasks;
- OpenAI provider config detects missing API key without leaking the key;
- `GET /ai/config` reports configured booleans only;
- unsupported provider returns a controlled error;
- no live provider calls happen in tests.

### 6. Optional manual smoke script or docs

Add documentation for a manual OpenAI smoke test, but do not run it.

The smoke test should be opt-in with something like:

```bash
AI_PROVIDER=openai OPENAI_ENABLE_LIVE_TESTS=true pytest ai-api/tests/test_openai_live.py
```

If adding a live test file, skip it unless explicitly enabled and key is present.

### 7. Docs

Update:

- `ai-api/README.md`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md` if useful
- `.env.example`

Document:

- mock is default;
- OpenAI is the first real provider;
- default OpenAI model is `gpt-5.4-nano`;
- fallback is `gpt-5.4-mini`;
- automated tests never require live provider keys;
- cost controls: small prompts, deterministic retrieval first, output caps, manual live tests only.

### 8. Validation

Run local validation only:

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct pytest is unavailable, the repo validator must still run the tests in its temporary venv and the limitation must be recorded.

Do not run live OpenAI calls, deployment workflows, cloud commands, or `docker compose up`.

## Outbox report

Create:

```text
outbox/0019-add-ai-provider-harness-openai-nano-results.md
```

Include:

- Summary of implementation.
- Files created/modified.
- Provider interface summary.
- Mock provider behavior.
- OpenAI provider readiness and limitations.
- Cost-control defaults.
- Validation commands and results.
- Recommended next task.

## Commit

Commit with:

```bash
git add inbox/0019-add-ai-provider-harness-openai-nano.md ai-api docs .env.example outbox/0019-add-ai-provider-harness-openai-nano-results.md
git commit -m "mailbox: complete task 0019 add ai provider harness openai nano"
git push origin main
```

## Done criteria

- Mock provider is the default provider.
- Provider interface exists and is tested.
- OpenAI provider path exists and is configured for `gpt-5.4-nano` by default.
- `gpt-5.4-mini` is documented/configured as fallback.
- Automated tests pass without live API keys.
- No live AI calls are run during validation.
- Config endpoints do not leak secrets.
- Documentation explains manual live testing and cost controls.
- Outbox report exists.
- Changes are committed and pushed.
