# Recipe Session Alpha Acceptance Runbook

## Purpose

Use this runbook to demo and validate the local Recipe Session Alpha workflow. The alpha layer lets an operator start a short-lived recipe creation session, inspect interpreted requirements, answer one clarification, send a follow-up, see whether RAG refreshed, and finalize for demo.

This is local and offline-friendly. Sessions are process-local, bounded, and expire. `Finalize for demo` does not write to production cookbook storage.

## Boundary

Normal validation uses:

- mock provider mode;
- generated saved-recipe and dataset fixtures;
- process-local in-memory session state;
- deterministic offline evals.

The alpha does not include production storage, persistent user memory, auth, paid access, public route exposure, Cloudflare changes, Redis, Postgres, SQLite session persistence, vector databases, embeddings, invite flows, provider budget enforcement, or a full chat UI.

If any future task wants to expose a recipe-session path publicly, it must first pass [AI Public Route Exposure Review](ai-public-route-exposure-review.md) and a new proxy/CORS/rate-limit review.

The locked combined 29/30 baseline is covered by [29/30 Integrated Regression And E2E Harness](ai-29-30-regression-e2e-harness.md) and `scripts\run-ai-29-30-regression.ps1`. That harness keeps the baseline offline by default and checks the recipe-session alpha together with operator gate, invite sessions, budget controls, usage reporting, route exposure assumptions, and monetization boundaries before any future secondary-provider offload work.

## Start The Mock Demo

Run the canonical offline smoke command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

Start the local browser demo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Open:

```text
http://127.0.0.1:8000/demo
```

Use mock provider mode for acceptance unless a separate live-provider task explicitly opts in.

## Happy Path

In the `Recipe Session Alpha` panel, start with:

```text
classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight
```

Expected:

- `response_state=draft_generated`;
- `confidence_label=high`;
- dish intent and serving count are visible;
- draft summary is present;
- citations and support metadata appear when generated fixtures retrieve matches;
- no raw prompts, provider responses, secrets, local paths, or stack traces appear.

## Clarification Path

Start with:

```text
make dessert
```

Expected:

- `response_state=clarification_needed`;
- exactly one bounded question is visible;
- no fake draft is shown;
- follow-up input remains enabled.

Answer with:

```text
cheesecake, no-bake, for 4 people
```

Expected:

- requirements update with cheesecake and no-bake method;
- RAG runs because the clarification changes retrieval intent;
- a draft is generated when the input is specific enough;
- retrieval query keeps the no-bake method signal;
- draft instructions stay in chill/refrigerate/serve-cold style behavior;
- draft instructions do not mention `preheat`, `oven`, `bake`, or `center is just set`.

## RAG Refresh Path

Start with the baked cheesecake happy-path input, then send:

```text
actually make it no-bake
```

Expected:

- `response_state=rag_refreshed` or `draft_revised`;
- `rag_refreshed=true`;
- changed fields include `cooking_method`;
- refresh reason explains the material method change;
- current citations/support info remains safe and visible;
- the revised draft preserves the no-bake constraint through retrieval query building, importer draft shaping, and finalize/demo display.

Equipment and exclusion follow-ups should also refresh when they affect retrieval intent:

```text
use air fryer instead
no nuts
no heavy cream
```

## No-Refresh Path

After a generated draft, send any of:

```text
thanks
looks good
make it shorter
```

Expected:

- `response_state=no_material_change`;
- `rag_refreshed=false`;
- no new draft is required;
- UI copy should not imply a provider call happened.

## Finalize For Demo

After a generated draft, click `Finalize for demo`.

Expected:

- `response_state=ready_to_finalize`;
- warning says no production cookbook write-back occurred;
- repeated finalize does not duplicate the warning.

If there is no generated draft yet, finalize should keep the session in a clarification-style state and warn that no generated draft is available.

## Missing And Expired Sessions

Unknown or expired session IDs should return a safe `404` / `not_found` response for get, message, and finalize. The UI should show a friendly recoverable error and invite the operator to start a new local alpha session.

## What Good Looks Like

- Interpreted requirements are understandable.
- One-question clarification appears only when input is too vague or materially ambiguous.
- Material changes refresh RAG and explain why.
- Chatter and formatting-only requests do not refresh RAG.
- Citations and RAG support labels remain visible but are not described as authoritative when support is weak.
- Logs and API/UI responses expose only safe operational metadata.

## Validation Commands

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
bash scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke and live eval wrappers should skip cleanly unless explicit live opt-in settings are present.

## Windows Note

Direct Windows pytest may fail before test execution on some machines because of the known local `pytest-of-scott` temporary-directory ACL issue. When that happens, treat the Git Bash validator path as the authoritative normal-validation path if it passes.
