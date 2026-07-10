# 0030D Recipe Session Demo UI And E2E Smoke Results

## Summary

Added a local `Recipe Session Alpha` section to the existing AI sidecar demo UI. The panel lets an operator start a recipe session, send a follow-up, get current session state, finalize for demo, and reset local UI state without adding production storage or a full chat UI.

## UI Section Added

- Added initial recipe notes and follow-up textareas.
- Added `Start session`, `Send follow-up`, `Get session`, `Finalize for demo`, and `Reset session` controls.
- Added loading, friendly recoverable error, and reset behavior.
- Kept the section local/operator-focused and mock-friendly.

## Response States Displayed

The UI now displays safe session fields including:

- `interaction_id`
- `response_state`
- `revision_count`
- `confidence_label`
- interpreted requirements
- open and resolved questions
- `rag_refreshed`
- `rag_refresh_reason`
- `changed_fields`
- `support_level`
- derived `last_citation_ids`
- `expires_at`
- warnings

When present, the panel also renders the draft summary, citations/provenance, retrieval metadata, and support/citation labels using the same safe display helpers as the importer UI.

## Clarification Behavior

Vague input such as `make dessert` returns `clarification_needed`, shows one bounded clarification question, and does not render a fake draft.

## RAG Refresh Behavior

A material follow-up such as `actually make it no-bake` after a baked cheesecake session displays RAG refresh/revision status, changed fields, refresh reason when provided, current draft state, citations, and support metadata.

## No-Refresh Behavior

Follow-ups such as `thanks`, `looks good`, or formatting-only changes display `no_material_change`, `rag_refreshed=false`, and a clear no-refresh explanation without implying a provider call happened.

## Finalize Behavior

`Finalize for demo` calls the alpha finalize endpoint and displays `ready_to_finalize` plus the demo-only warning. It does not write to production cookbook storage.

## Mock Smoke Coverage

Updated `scripts/demo-ai-mock.ps1` to exercise the recipe-session endpoint flow offline:

- detailed cheesecake start -> `draft_generated`
- no-bake follow-up -> `rag_refreshed`
- get session -> safe state
- finalize -> `ready_to_finalize`
- vague dessert start -> `clarification_needed`
- chatter follow-up -> `no_material_change`

The smoke script also checks response text for forbidden secret-like markers.

## Tests Added Or Updated

- Extended `ai-api/tests/test_demo_ui.py` to assert the Recipe Session Alpha section and controls exist.
- Added static JS coverage for session endpoint calls and render paths for `clarification_needed`, `rag_refreshed`, `draft_revised`, `no_material_change`, and `ready_to_finalize`.
- Preserved forbidden-text checks for static assets.
- Existing 0030C API tests remain covered by the full Git Bash validator.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` - passed, 28/28 offline evals.
- Focused direct Windows static UI pytest subset - passed, 4 selected tests.
- Direct Windows pytest for tmp-fixture tests hit the known local `pytest-of-scott` temp ACL issue: `PermissionError: [WinError 5] Access is denied`.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` - passed, including 210 pytest tests and 28 offline evals.
- `git diff --check` - passed.
- `docker compose config --quiet` - passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` - passed, including the new recipe-session smoke flow.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` - skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` - skipped cleanly without live opt-in.

## Explicit Non-Goals

No production storage, database migrations, auth, paid access, public route exposure, persistent user memory, Redis, Postgres, SQLite session persistence, vector DB, embeddings, Qdrant, pgvector, full chat UI, browser automation, screenshots, or live OpenAI calls were added.

## Artifact Safety Confirmation

No raw dataset files, generated live artifacts, screenshots, logs, credentials, environment files, raw provider prompts, local absolute dataset paths in public UI, disk cache, persistent indexes, or production session storage were committed.
