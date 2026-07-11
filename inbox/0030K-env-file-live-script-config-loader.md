# 0030K Env File Live Script Config Loader

## Goal

Improve local live/demo script ergonomics by allowing the PowerShell wrappers and live-eval scripts to load configuration from a user-provided local `.env` file path, and optionally write safe missing defaults to that `.env` file.

This task is a follow-up to `0030J 29/30 Integrated Regression And E2E Harness`.

The problem:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
# Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
# SKIP: OPENAI_ENABLE_LIVE_TESTS=true is required.
# Required live eval settings: AI_PROVIDER=openai, OPENAI_ENABLE_LIVE_TESTS=true,
# OPENAI_API_KEY present, OPENAI_LIVE_TEST_BUDGET_CENTS within 1-25,
# OPENAI_MODEL configured, and AI_MAX_OUTPUT_TOKENS between 1 and 300.
```

The local `.env` may already contain values such as:

```text
ORIGIN=https://cookbook.roadmaps.link
CLOUDFLARE_TUNNEL_TOKEN=replace_me
PUID=1000
PGID=1000

AI_PROVIDER=mock
AI_MODEL=mock-basic
AI_MAX_OUTPUT_TOKENS=700
AI_TIMEOUT_SECONDS=20
OPENAI_API_KEY=sk-proj-REDACTED
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
OPENAI_ENABLE_LIVE_TESTS=false
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OLLAMA_BASE_URL=
```

Do **not** commit any real `.env` file or real key. Treat the above as an example only. Never include a real key in docs, tests, logs, output, or outbox.

## Primary Objective

Add a safe `.env` file loader and missing-default initializer so the local scripts can run from a configured `.env` file instead of requiring repeated command-line arguments.

Desired user experience examples:

```powershell
# Load values from a local ignored .env file, but do not modify it.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env

# Load values from .env and append safe missing defaults only.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env -WriteMissingEnvDefaults

# Same for live evals.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env

# Same for the 29/30 regression wrapper, while keeping normal regression offline by default.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ai-29-30-regression.ps1 -EnvFile .\.env
```

## Non-Negotiable Boundaries

Do not add:

- committed `.env` files;
- committed API keys;
- committed key fragments;
- committed secrets;
- printing of `.env` values;
- printing of `OPENAI_API_KEY` or any provider key;
- automatic live opt-in without an explicit `.env` value or explicit switch;
- GLM provider integration;
- secondary-provider routing;
- production auth;
- user accounts;
- paid access;
- payment integration;
- ad/sponsor runtime code;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- database migrations;
- production storage;
- Redis/Postgres/SQLite persistence;
- live OpenAI calls during normal validation.

Live checks must remain explicit opt-in.

If `OPENAI_ENABLE_LIVE_TESTS=false`, the live scripts must still skip cleanly even when `-EnvFile .\.env` is supplied.

## Suggested Files

Likely new files:

```text
scripts/lib/ai-env-file.ps1
scripts/test-ai-env-file-loader.ps1
ai-api/tests/test_ai_env_file_script_docs.py
outbox/0030K-env-file-live-script-config-loader-results.md
```

Likely updated files:

```text
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
scripts/run-ai-29-30-regression.ps1
scripts/start-ai-demo-local.ps1 if useful and safe
scripts/demo-ai-mock.ps1 only if needed
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/live-openai-demo-evals.md
docs/ai-29-30-regression-e2e-harness.md
docs/ai-feature-status.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
```

## Required Work

### 1. Add shared PowerShell `.env` helper

Create:

```text
scripts/lib/ai-env-file.ps1
```

Implement safe helpers such as:

```powershell
Import-AiEnvFile -Path <path> -OnlyIfMissing
Write-AiEnvDefaults -Path <path> -Defaults <hashtable> -OnlyMissing
Test-AiEnvFilePath -Path <path>
Get-AiSafeEnvSummary
```

Requirements:

- parse simple `KEY=value` lines;
- ignore blank lines;
- preserve comments;
- preserve existing values;
- do not overwrite existing values unless a future explicit force switch is added, which is not required here;
- do not print secret values;
- support quoted and unquoted values if easy;
- handle Windows paths safely;
- fail clearly if the supplied env file path does not exist, unless `-WriteMissingEnvDefaults` is creating the file intentionally;
- never add the file to Git;
- never stage or commit `.env`.

Secret-like variable names must be redacted in summaries:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
CLOUDFLARE_TUNNEL_TOKEN
*_SECRET*
*_TOKEN*
*_KEY*
*_PASSWORD*
```

### 2. Add `-EnvFile` to local live scripts

Update:

```text
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
```

Add parameters:

```powershell
param(
  [string]$EnvFile,
  [switch]$WriteMissingEnvDefaults
)
```

Behavior:

- if `-EnvFile` is provided, load values from that file into the current PowerShell process environment;
- loaded values should only fill variables that are currently missing or empty by default;
- existing process environment values should win over file values;
- script-specific command-line arguments should still win over both process env and file env;
- never print values loaded from `.env`;
- print only safe summary text, such as:

```text
Loaded environment from .env: AI_PROVIDER=set, OPENAI_ENABLE_LIVE_TESTS=set, OPENAI_API_KEY=redacted-present, OPENAI_MODEL=set
```

Do not print actual values.

### 3. Add safe missing defaults writer

When `-WriteMissingEnvDefaults` is supplied, append missing non-secret defaults to the target `.env` file.

For live OpenAI smoke/evals, suggested missing defaults:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=false
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
AI_MAX_OUTPUT_TOKENS=300
AI_TIMEOUT_SECONDS=60
OPENAI_LIVE_TEST_BUDGET_CENTS=25
AI_PROVIDER_CALLS_ENABLED=true
AI_PROVIDER_GLOBAL_DISABLE=false
AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION=2
AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL=12000
AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL=300
AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL=14000
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION=0.25
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL=0.05
AI_PROVIDER_BUDGET_MODE=enforce
```

Important:

- Do not write `OPENAI_API_KEY` automatically.
- Do not write fake API keys.
- Do not write `OPENAI_ENABLE_LIVE_TESTS=true` automatically.
- Do not overwrite `AI_PROVIDER=mock` automatically unless the user explicitly edits the `.env` or a future explicit `-SetLiveOpenAI` switch is designed.
- If `AI_PROVIDER=mock` remains in `.env`, the live scripts should clearly explain that live OpenAI requires `AI_PROVIDER=openai`.
- If `OPENAI_ENABLE_LIVE_TESTS=false` remains in `.env`, live scripts should skip cleanly and explain that this is expected.

### 4. Add `-EnvFile` to 29/30 regression wrapper

Update:

```text
scripts/run-ai-29-30-regression.ps1
```

Behavior:

- allow `-EnvFile` for consistent ergonomics;
- by default, 29/30 regression remains offline/mock;
- if env file contains live values, the regression wrapper must still keep normal validation offline unless the wrapper's explicit live-smoke switch is used;
- no accidental live calls;
- no printed secrets.

### 5. Optional: update start script safely

If useful, update:

```text
scripts/start-ai-demo-local.ps1
```

Add `-EnvFile` support only if it does not destabilize existing behavior.

Precedence should be:

```text
explicit script arguments > existing process environment > values loaded from EnvFile > script defaults
```

Document this clearly.

### 6. Add tests

Add script-level and doc-level tests.

Create:

```text
scripts/test-ai-env-file-loader.ps1
```

It should use a temporary `.env.test` file with fake values only.

Test cases:

- loads missing variables from env file;
- does not overwrite existing process env values;
- appends missing defaults only;
- preserves comments and existing lines;
- does not write `OPENAI_API_KEY` automatically;
- redacts keys/tokens/secrets in safe summary output;
- handles `OPENAI_ENABLE_LIVE_TESTS=false` without forcing live mode;
- handles missing env file with a clear error;
- avoids printing fake key values.

Create:

```text
ai-api/tests/test_ai_env_file_script_docs.py
```

Test cases:

- updated scripts expose `-EnvFile`;
- live docs explain `.env` loading;
- docs say live opt-in remains explicit;
- docs say no secrets are printed;
- docs say `.env` stays ignored/uncommitted;
- docs do not include real key examples.

Forbidden strings in committed docs/outbox/tests:

```text
sk-proj-
sk_live_
sk_test_
STRIPE_SECRET_KEY
PAYPAL_CLIENT_SECRET
raw_provider_prompt
raw_provider_response
Authorization: Bearer real
```

A fake placeholder like `OPENAI_API_KEY=replace_me` is acceptable only in `.env.example`-style documentation if already consistent with repo style. Prefer not to add new key examples.

### 7. Update docs

Update:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/live-openai-demo-evals.md
docs/ai-29-30-regression-e2e-harness.md
docs/ai-feature-status.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
```

Document:

- `-EnvFile .\.env` usage;
- `-WriteMissingEnvDefaults` usage;
- exact precedence rules;
- how to intentionally enable live tests by editing local ignored `.env`;
- why `OPENAI_ENABLE_LIVE_TESTS=false` still skips;
- why `AI_PROVIDER=mock` still skips/does not run OpenAI;
- no secret printing;
- `.env` remains ignored and uncommitted;
- normal validation remains mock/offline.

Add a safe example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env -WriteMissingEnvDefaults

# Then manually edit local ignored .env only if you intend live calls:
# AI_PROVIDER=openai
# OPENAI_ENABLE_LIVE_TESTS=true
# OPENAI_API_KEY=<set locally, never commit or paste>

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env
```

Do not include real keys.

### 8. Add outbox report

Create:

```text
outbox/0030K-env-file-live-script-config-loader-results.md
```

Include:

- scripts updated;
- helper behavior;
- `.env` load behavior;
- missing-default writer behavior;
- precedence rules;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- `demo-ai-live-smoke.ps1` accepts `-EnvFile`.
- `run-openai-demo-evals.ps1` accepts `-EnvFile`.
- `run-ai-29-30-regression.ps1` accepts `-EnvFile` while staying offline/mock by default.
- Missing safe defaults can be appended with `-WriteMissingEnvDefaults` without overwriting existing values.
- No real API key is written by helper defaults.
- No script prints secret values.
- Existing process env and explicit script args take precedence over env-file values.
- Live tests still require explicit opt-in.
- `OPENAI_ENABLE_LIVE_TESTS=false` still skips cleanly.
- `AI_PROVIDER=mock` does not accidentally trigger OpenAI calls.
- Tests cover parsing, precedence, default writing, redaction, and no-secret behavior.
- Docs explain the workflow.
- No `.env` file, key, token, log, screenshot, generated artifact, live provider output, or local secret material is committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ai-29-30-regression.ps1 -EnvFile .\.env
& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_env_file_script_docs.py -q
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Expected behavior for normal validation:

- live scripts skip cleanly unless `.env` explicitly has `OPENAI_ENABLE_LIVE_TESTS=true`, `AI_PROVIDER=openai`, a locally configured `OPENAI_API_KEY`, and budget values in range;
- no key values are printed;
- normal mock/offline validation still passes.

Before committing, confirm:

- no `.env` file is staged;
- no real key is staged;
- no `sk-proj-`, `sk_live_`, or `sk_test_` string is staged;
- no secret-bearing output is in docs/outbox/tests;
- no GLM provider code is added;
- no secondary-provider routing is added;
- no payment/ad/sponsor runtime code is added;
- no public route exposure is added;
- no production auth/storage changes are added;
- no live calls are added to normal validation.

## Commit

```bash
git add scripts ai-api docs README.md outbox/0030K-env-file-live-script-config-loader-results.md

git commit -m "mailbox: complete task 0030K env file live script config loader"

git pull --rebase origin main
git push origin main
```
