# 0030I-6 Local Live Runtime Profile And Secret Injection

## Goal

Make the local integrated Cookbook AI product start in live OpenAI mode from local ignored configuration, without requiring a long list of command-line arguments every time.

The intended local operator experience should become:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

When the local ignored runtime configuration is present and valid, the server should start with:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_MODEL=gpt-5.4-nano
AI_MAX_OUTPUT_TOKENS within live cap
OPENAI_LIVE_TEST_BUDGET_CENTS within 1-25
OPENAI_API_KEY present but never printed
```

The only live model remains:

```text
gpt-5.4-nano
```

Mock/offline must remain available for validation and demos, but the local product should no longer require repeated `-Provider openai -EnableLiveTests -OpenAIModel ...` arguments to run with the live agent.

## Background

Earlier work added:

- `/product` as the local integrated product shell;
- `/demo` as the AI workspace;
- a Live/Mock UI selector;
- request-scoped AI mode routing across importer, Recipe Session, Ask, Dataset Ask, and Meal Planner;
- safe `503` behavior when Live is selected but the server was started without live opt-in/configuration;
- an env-file loader for live smoke/eval wrappers.

The current gap is startup ergonomics and secure local secret injection:

- the product UI can request live mode;
- routes can safely use live mode when configured;
- but `scripts/start-ai-demo-local.ps1` still commonly starts as `Provider: mock`, forcing Live UI requests into expected 503 unavailable behavior;
- the user wants local live mode to be the default when local ignored configuration authorizes it.

## Primary Objective

Implement a local runtime profile system for `scripts/start-ai-demo-local.ps1` that safely loads local ignored config and injects it into the AI sidecar process environment.

This is local development/runtime ergonomics only. Do not add production auth, public routes, AWS resources, Cloudflare changes, payment, or deployment automation.

## Required Work

### 1. Inspect current live/env configuration support

Inspect:

```text
scripts/start-ai-demo-local.ps1
scripts/lib/ai-env-file.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
scripts/demo-ai-mock.ps1
.env.example
.gitignore
ai-api/app/config.py
ai-api/app/ai_mode_routing.py
docs/ai-live-demo-runbook.md
docs/local-cookbook-ai-product-integration.md
docs/live-openai-smoke-tests.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Confirm how these are currently resolved:

```text
AI_PROVIDER
AI_MODEL
OPENAI_ENABLE_LIVE_TESTS
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_LIVE_TEST_BUDGET_CENTS
AI_MAX_OUTPUT_TOKENS
AI_TIMEOUT_SECONDS
AI_PROVIDER_CALLS_ENABLED
AI_PROVIDER_GLOBAL_DISABLE
AI_PROVIDER_BUDGET_MODE
```

### 2. Define the local runtime profile contract

Add a clear local runtime contract for the start script.

Acceptable design:

```text
.env                         -> ignored local secrets and runtime values
config/ai-runtime.local.json -> ignored local non-secret runtime profile, optional
config/ai-runtime.example.json -> committed safe template, no secrets
```

Use different names if the repo already has a preferred pattern.

Requirements:

- real `.env` must remain ignored and uncommitted;
- real local runtime profile containing machine-specific choices should remain ignored if it can include sensitive or private values;
- committed example/spec file must not contain secrets;
- `OPENAI_API_KEY` must never be written automatically;
- no real keys, key fragments, tokens, or provider secrets may appear in committed files, logs, tests, docs, or outbox.

The profile should support safe non-secret settings such as:

```json
{
  "default_provider": "openai",
  "default_model": "gpt-5.4-nano",
  "enable_live_tests": true,
  "max_output_tokens": 300,
  "live_test_budget_cents": 25,
  "timeout_seconds": 60,
  "budget_mode": "enforce"
}
```

If JSON/profile parsing is too much for this task, use `.env` only and document a follow-up for an optional spec file. Prefer a simple, reliable implementation over a complex config system.

### 3. Update `start-ai-demo-local.ps1` to load local config by default

Update the start script so it automatically attempts to load safe local runtime config.

Desired behavior:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

should:

1. look for a local ignored `.env` by default;
2. optionally look for a local ignored runtime profile/spec file if implemented;
3. load values into the PowerShell process environment without printing secrets;
4. launch the AI sidecar so Uvicorn inherits the resolved environment;
5. print a safe startup summary.

Startup summary should show only safe facts:

```text
Provider: openai
Model: gpt-5.4-nano
Live tests enabled: true
OpenAI API key: redacted-present
Budget cents: 25
Max output tokens: 300
AI timeout seconds: 60
```

It must not print:

- API key;
- key prefix/suffix;
- `.env` contents;
- local filesystem secrets beyond already-safe repo-relative fixture paths;
- raw provider prompts;
- raw provider responses.

### 4. Preserve explicit override and mock validation behavior

Even if local default becomes live when config exists, these must remain true:

- `scripts/demo-ai-mock.ps1` forces or verifies mock/offline mode;
- Git Bash validator remains offline/mock-only;
- offline evals never call live OpenAI;
- live smoke/eval wrappers still require explicit live opt-in and budget limits;
- command-line arguments, when provided, override env/profile defaults;
- existing process environment values take precedence over local file values unless an explicit force behavior already exists;
- browser selection alone still cannot bypass server-side live opt-in/key/budget checks.

Precedence should be documented clearly. Recommended:

```text
explicit script arguments > existing process environment > local runtime profile > local .env > script defaults
```

If the existing env helper uses a different safe precedence, preserve it and document the actual behavior.

### 5. Add safe config initialization support

Add a safe helper mode if useful, such as:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -WriteMissingLiveDefaults
```

or reuse the existing `-WriteMissingEnvDefaults` convention.

This may append missing safe defaults to `.env` or create a local ignored profile.

It may write:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_MODEL=gpt-5.4-nano
AI_MAX_OUTPUT_TOKENS=300
AI_TIMEOUT_SECONDS=60
OPENAI_LIVE_TEST_BUDGET_CENTS=25
AI_PROVIDER_CALLS_ENABLED=true
AI_PROVIDER_GLOBAL_DISABLE=false
AI_PROVIDER_BUDGET_MODE=enforce
```

It must not write:

```text
OPENAI_API_KEY=<anything>
```

Instead, it should print safe guidance:

```text
Add OPENAI_API_KEY to your local ignored .env or process environment. Never commit or paste it.
```

Do not auto-enable live in CI/normal validation scripts.

### 6. Add secure injection documentation

Document how secrets are injected into the web server process locally:

- the launcher reads ignored local config;
- it sets process environment variables for the child Uvicorn process;
- the key is never passed in a URL, request body, browser storage, static JS, or committed file;
- the browser only sends safe mode/model preferences;
- server-side config controls whether live calls are allowed.

Also document future production direction without implementing it:

- production should use a managed secret store or deployment secret mechanism;
- do not rely on committed env files;
- do not expose provider keys to the browser.

### 7. Add tests

Add deterministic tests for:

- `start-ai-demo-local.ps1` exposes or uses automatic local env/profile loading;
- safe startup summary redacts `OPENAI_API_KEY`;
- default live local config resolves to `openai/gpt-5.4-nano` when `.env` or profile has required values;
- missing API key produces safe missing-key guidance, not a crash with raw values;
- explicit mock override still works;
- mock smoke remains mock/offline;
- normal validator/evals remain offline/mock-only;
- committed docs/scripts do not contain real key patterns;
- `.env` remains ignored;
- profile example contains no secrets.

Use fake placeholder values only in tests. Do not make live OpenAI calls.

### 8. Update docs

Update:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
.env.example if appropriate and safe
.gitignore if a local runtime profile/spec path is added
```

Docs should explain:

- default local live startup from ignored config;
- exact local `.env` keys required;
- optional profile/spec behavior if implemented;
- how to initialize safe defaults;
- where to place `OPENAI_API_KEY` securely;
- how to force mock/offline mode;
- why UI Live selection still returns 503 if the server was not started with valid live config;
- no secrets in browser/static files;
- no secrets committed.

### 9. Add outbox report

Create:

```text
outbox/0030I-6-local-live-runtime-profile-and-secret-injection-results.md
```

The outbox must summarize:

- local live runtime profile/config behavior;
- start script behavior;
- secret injection model;
- precedence rules;
- default live startup behavior;
- mock override behavior;
- tests added;
- validation results;
- explicit non-goals;
- any follow-up needed.

## Acceptance Criteria

- `scripts/start-ai-demo-local.ps1` can start the local sidecar in live OpenAI mode from local ignored `.env` and/or local runtime profile without requiring long CLI arguments.
- The live local default uses only `gpt-5.4-nano`.
- `OPENAI_API_KEY` is injected into the Uvicorn process via server-side environment only and is never exposed to the browser or committed files.
- Startup summary redacts the API key.
- Missing or invalid live config produces clear safe guidance.
- Mock/offline mode remains available and can be forced for validation.
- Normal validation remains offline/mock-only.
- Existing live smoke/eval wrappers keep explicit opt-in and budget caps.
- UI Live selection no longer produces confusing 503s when the local server was intended to be live and config is valid.
- UI Live selection still produces controlled safe unavailable behavior when live config is missing or invalid.
- No real `.env`, API key, token, key fragment, provider output, raw prompt, local secret file, screenshot, or generated artifact is committed.
- No AWS/platform work, production auth, payment, public route exposure, Cloudflare/DNS change, secondary-provider runtime, vector DB, embeddings, upstream UI rewrite, browser automation, raw dataset commit, persistent index, or disk cache is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The normal validator and mock demo must not call live OpenAI.

Live smoke/eval wrappers should still skip unless explicitly opted in through valid local config.

If a local fake `.env` fixture is used for tests, use a temp file and fake values only.

## Commit

```bash
git add ai-api docs README.md scripts .env.example .gitignore config outbox/0030I-6-local-live-runtime-profile-and-secret-injection-results.md

git commit -m "mailbox: complete task 0030I-6 local live runtime profile secret injection"

git pull --rebase origin main

git push origin main
```
