# 0029D Local Operator Access Gate Results

## Summary

Implemented the first local/private operator gate for the AI demo workflows. The gate is opt-in, disabled by default, and uses safe fingerprint comparison for token/header verification without leaking raw tokens or local paths.

## What Was Implemented

- `ai-api/app/ai_operator_gate.py` adds the reusable gate helper, safe decision model integration, constant-time fingerprint comparison, and safe HTTP exception shaping.
- `ai-api/app/ai_access_models.py` adds `AiOperatorGateDecision` and `AiOperatorGateStatus`.
- `ai-api/app/config.py` adds operator-gate settings and environment parsing.
- `ai-api/app/main.py` protects importer, dataset ask, and meal-plan routes when the gate is enabled.
- `ai-api/app/recipe_session_routes.py` protects recipe-session start/message/get/finalize routes when the gate is enabled.
- `scripts/demo-ai-mock.ps1` pins the gate off so mock/offline smoke stays stable in a dirty shell.

## Gate Behavior

- gate disabled: requests pass through unchanged;
- enabled + local bypass + local/TestClient request: allowed;
- enabled + missing fingerprint config: misconfigured;
- enabled + missing token: blocked;
- enabled + mismatched fingerprint: blocked;
- enabled + matching `X-AI-Operator-Token` or `Authorization: Bearer ...`: allowed;
- unsupported workflows are blocked when the gate is enabled.

## Safe Metadata Exposed

- enabled/allowed/status/reason/workflow;
- grant type / token source label;
- short metadata fingerprint;
- safe metadata only, such as local/remote host kind.

No raw tokens, headers, API keys, env values, local absolute paths, request bodies, or stack traces are returned by the helper or API responses.

## Tests Added

- `ai-api/tests/test_ai_operator_gate.py`
- `ai-api/tests/test_ai_access_models.py` extended with `AiOperatorGateDecision`

The tests cover:

- gate disabled behavior;
- local bypass behavior;
- missing-token blocks;
- header and bearer token acceptance;
- disallowed workflow handling;
- misconfigured gate handling;
- importer and recipe-session route protection;
- meal-plan route blocking;
- safe serialization / no secret leakage.

## Docs Updated

- `docs/ai-local-operator-access-gate.md`
- `docs/ai-session-metering-schema.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

## Validation Results

- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed.
- Git Bash validation ran the full offline pytest suite and offline evals successfully: 240 pytest cases passed and 39/39 eval cases passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly because live opt-in was not present.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly because live opt-in was not present.
- Direct Windows pytest was also attempted and hit the known `pytest-of-scott` temp ACL issue. That was documented separately and does not change the Git Bash validation result.

## Explicit Non-Goals

- no production auth;
- no user accounts or login UI;
- no OAuth/OIDC;
- no paid access or invite emails;
- no payment integration;
- no public route exposure;
- no Cloudflare changes;
- no database migrations;
- no production storage;
- no persistent user memory;
- no Redis/Postgres/SQLite session persistence;
- no runtime budget enforcement;
- no admin dashboard UI;
- no live OpenAI calls during normal validation.

## Artifact Safety Confirmation

- no secrets or tokens committed;
- no `.env` files committed;
- no raw provider prompts or responses committed;
- no screenshots or generated live artifacts committed;
- no raw dataset files committed;
- no persistent index or disk cache artifacts committed;
- no local absolute paths exposed in public docs examples.
