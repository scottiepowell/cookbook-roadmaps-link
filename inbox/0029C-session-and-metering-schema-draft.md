# 0029C Session And Metering Schema Draft

## Goal

Draft the local/offline schema layer for future AI demo access control, session tracking, metering, and admin audit events without enabling public live AI, production billing, auth, paid access, or public route exposure.

This task is design-plus-schema-scaffold only. It should create safe models, migration-neutral documentation, and deterministic tests that prepare the project for later operator-gated and invite-only access tasks.

## Context

The completed 0029B/0030 work now provides a strong local AI demo and recipe-session alpha:

- RAG-informed importer with citations/provenance;
- retrieval relevance tuning;
- bounded context packing;
- dataset normalization;
- RAG support/honesty policy;
- local in-memory retrieval cache;
- offline RAG E2E tests;
- recipe-session requirements architecture;
- recipe-session deterministic scaffold;
- recipe-session alpha API endpoints;
- Recipe Session Alpha demo UI;
- recipe-session offline eval harness.

The next risk boundary is controlled access and cost observability. Before implementing an operator gate, invite flow, or provider budget enforcement, define the local schemas/events that future tasks will use.

## Primary Objective

Create schema drafts and deterministic tests for:

```text
AI demo session
access grant
provider meter event
quality/eval event
admin audit event
budget snapshot
```

The work should make future access/metering tasks easier without turning on live/public access.

## Non-Negotiable Boundaries

Do not add:

- production storage;
- database migrations;
- auth;
- paid access;
- public route exposure;
- Cloudflare changes;
- persistent user memory;
- Redis;
- Postgres;
- SQLite persistence unless explicitly limited to documentation examples only;
- payment provider integration;
- invite emails;
- live OpenAI calls during normal validation;
- budget enforcement runtime;
- admin dashboard UI;
- public API keys or secrets.

This task should not enable anyone outside the local/operator workflow to access live AI.

## Suggested Files

Likely new files:

- `ai-api/app/ai_access_models.py`
- `ai-api/tests/test_ai_access_models.py`
- `docs/ai-session-metering-schema.md`
- `outbox/0029C-session-and-metering-schema-draft-results.md`

Likely updated files:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md` if relevant
- `docs/ai-live-demo-runbook.md` if relevant
- `README.md` if relevant

## Required Work

### 1. Add schema/model module

Create a schema module for future AI access and metering concepts.

Suggested file:

```text
ai-api/app/ai_access_models.py
```

Use Pydantic models or dataclasses consistent with the existing project style.

The models should be safe to serialize, deterministic in tests, and independent from production databases.

### 2. Define AI demo session model

Define an `AiDemoSession` model or equivalent.

Suggested fields:

- `session_id`
- `session_type`, such as `local_operator`, `invite`, `public_preview`
- `status`, such as `active`, `expired`, `revoked`, `completed`
- `created_at`
- `expires_at`
- `revoked_at`
- `revoked_reason`
- `operator_label`
- `access_grant_id`
- `request_count`
- `provider_call_count`
- `estimated_cost_usd`
- `last_activity_at`
- `metadata_fingerprint`

Do not include user secrets, API keys, raw IP addresses by default, raw provider prompts, raw provider responses, or long-term user memory.

### 3. Define access grant model

Define an `AiAccessGrant` model or equivalent.

Suggested fields:

- `grant_id`
- `grant_type`, such as `local_operator`, `invite_code`, `admin_override`
- `status`, such as `active`, `expired`, `revoked`, `used`
- `created_at`
- `expires_at`
- `used_at`
- `revoked_at`
- `revoked_reason`
- `max_sessions`
- `max_provider_calls`
- `max_estimated_cost_usd`
- `allowed_workflows`, such as importer, dataset ask, recipe session
- `notes`
- `metadata_fingerprint`

Do not store plain invite codes or raw tokens in this model. If token-like fields are represented, use fingerprints/hashes only.

### 4. Define provider meter event model

Define an `AiProviderMeterEvent` model or equivalent.

Suggested fields:

- `event_id`
- `session_id`
- `workflow`
- `provider`
- `model`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `status`, such as `allowed`, `skipped`, `blocked`, `failed`
- `reason`
- `created_at`
- `request_id`
- `safe_metadata`

The event should support mock/offline workflows where cost is zero or missing.

Do not include raw prompt text, raw provider response text, API keys, request bodies, or user secrets.

### 5. Define quality/eval event model

Define an `AiQualityEvent` or equivalent.

Suggested fields:

- `event_id`
- `session_id`
- `workflow`
- `eval_group`
- `case_id`
- `status`, such as `passed`, `failed`, `warning`, `skipped`
- `support_level`
- `retrieved_count`
- `citation_count`
- `warning_count`
- `latency_ms`
- `created_at`
- `safe_summary`

This should be suitable for future operator reports but not tied to any live dashboard yet.

### 6. Define admin audit event model

Define an `AiAdminAuditEvent` or equivalent.

Suggested fields:

- `event_id`
- `actor_label`
- `action`
- `target_type`
- `target_id`
- `created_at`
- `reason`
- `safe_metadata`

Example actions:

- `grant_created`
- `grant_revoked`
- `session_revoked`
- `provider_disabled`
- `budget_limit_changed`
- `live_access_enabled`
- `live_access_disabled`

Do not add an admin UI or real auth in this task.

### 7. Define budget snapshot model

Define an `AiBudgetSnapshot` or equivalent.

Suggested fields:

- `session_id`
- `grant_id`
- `provider_call_count`
- `max_provider_calls`
- `estimated_cost_usd`
- `max_estimated_cost_usd`
- `remaining_provider_calls`
- `remaining_estimated_cost_usd`
- `is_exhausted`
- `status_reason`
- `created_at`

This is a model only. Do not enforce budgets at runtime in this task.

### 8. Add safe serialization helpers

Add helpers or model methods that produce safe public/operator views.

Safe views should:

- include IDs, status, timestamps, counts, workflow names, model/provider names, and cost estimates;
- exclude secrets, env vars, raw prompts, raw responses, local paths, raw invite codes, raw tokens, stack traces, and private filesystem details;
- use fingerprints where identifiers are needed but raw values should not be exposed.

### 9. Add deterministic tests

Add tests for:

- creating each model with valid sample data;
- default values and statuses;
- budget snapshot remaining-call and remaining-cost calculations;
- exhausted budget behavior;
- provider meter event with mock/offline provider;
- provider meter event with token/cost data;
- access grant safe serialization excludes raw token/code fields;
- audit event safe serialization;
- quality event safe serialization;
- forbidden strings do not appear in serialized output.

Forbidden strings should include:

```text
OPENAI_API_KEY
sk-
Authorization
.env
.tmp-ai-demo
raw_provider_prompt
raw_provider_response
C:\\Users\\
/home/
postgres://
redis://
```

### 10. Add schema documentation

Create:

```text
docs/ai-session-metering-schema.md
```

The doc should explain:

- why these schemas exist;
- how they relate to the current local AI demo and recipe-session alpha;
- session model;
- access grant model;
- provider meter event model;
- quality/eval event model;
- admin audit event model;
- budget snapshot model;
- safe serialization rules;
- future tasks that can use these models;
- explicit non-goals.

### 11. Update backlog/docs

Update:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md` if relevant
- `docs/ai-live-demo-runbook.md` if relevant
- `README.md` if relevant

Mark `0029C` complete only after implementation and validation pass.

### 12. Create outbox report

Create:

```text
outbox/0029C-session-and-metering-schema-draft-results.md
```

Include:

- models added;
- safe serialization behavior;
- budget snapshot behavior;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Schema/model module exists for future AI demo sessions, access grants, metering, quality events, admin audit events, and budget snapshots.
- Models are deterministic and testable offline.
- Safe serialization excludes secrets, raw prompts, raw provider responses, local paths, raw tokens, and env values.
- Budget snapshot calculations are tested.
- Documentation explains how the schema layer will support future operator gate, invite flow, provider budget enforcement, and admin reports.
- Existing RAG/importer/session evals and tests still pass.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No production storage, database migrations, auth, paid access, public route exposure, Redis, Postgres, persistent memory, payment integration, or admin dashboard is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest is run and fails because of the known local `pytest-of-scott` temp ACL issue or because live OpenAI environment variables are set, document that separately and rely on Git Bash validation if it passes.

Before committing, confirm:

- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage;
- no payment or invite secrets.

## Commit

```bash
git add ai-api docs README.md outbox/0029C-session-and-metering-schema-draft-results.md

git commit -m "mailbox: complete task 0029C session and metering schema draft"

git pull --rebase origin main
git push origin main
```
