# 0030G Operator UX Requirement Diff And Revision Summaries

## Goal

Polish the local Recipe Session Alpha operator UX so multi-turn requirement changes are easier to understand during demos.

This task follows the completed 0030A-F line:

- `0030A`: requirements interaction architecture;
- `0030B`: requirements/session alpha scaffold;
- `0030C`: recipe-session alpha API endpoints;
- `0030D`: recipe-session demo UI and E2E smoke;
- `0030E`: recipe-session eval harness and regression baseline;
- `0030F`: alpha hardening and acceptance.

The current alpha can start a recipe session, ask bounded clarifying questions, classify follow-ups, refresh or reuse RAG, expose response states, and finalize for demo. The next improvement is operator clarity: when a user changes requirements, the demo should make the before/after change easy to see.

## Background

The `0030F` acceptance pass hardened API/UI behavior, expanded edge cases, and documented the local-only alpha boundary. It recommended a follow-on `0030G` task for operator UX polish around requirement diffs and revision summaries.

This task should stay local/offline and mock-friendly. Do not add production storage, authentication, paid access, public route exposure, persistent user memory, vector databases, embeddings, browser automation, screenshots, or live OpenAI calls.

## Primary Objective

Improve the Recipe Session Alpha demo/operator experience by showing:

- what requirements the system understood;
- what changed after a follow-up message;
- whether RAG refreshed or was reused;
- why the decision was made;
- what revision number the session is on;
- a short safe summary of the current draft state.

## Required Work

### 1. Add requirement diff summary model/helper

Add a deterministic helper that can compare previous and current recipe-session requirements.

Suggested location:

```text
ai-api/app/recipe_session.py
```

or a small dedicated helper module if cleaner.

The diff summary should identify changes in fields such as:

- dish intent;
- serving count;
- required ingredients;
- optional ingredients;
- excluded ingredients;
- cooking method;
- equipment constraints;
- time constraints;
- dietary constraints;
- texture/style goals;
- assumptions;
- open/resolved questions.

Suggested output fields:

- `changed_fields`;
- `added_requirements`;
- `removed_requirements`;
- `updated_requirements`;
- `summary_message`;
- `rag_refresh_relevant`;
- `rag_refresh_reason`;
- `previous_revision`;
- `current_revision`.

Keep messages short and safe.

### 2. Add revision summary helper

Add a helper that creates a concise revision summary for the operator UI.

Examples:

```text
Revision 2: Changed cooking method from baked to no-bake; RAG refreshed because method affects retrieval.
```

```text
Revision 3: Formatting-only follow-up; existing draft and citations were reused.
```

```text
Revision 4: Added excluded ingredient `nuts`; RAG refreshed because ingredient exclusions affect retrieval.
```

The summary should not expose raw prompts, provider responses, local paths, private env values, or long hidden internals.

### 3. Integrate into recipe-session API responses

Extend local alpha recipe-session responses with safe diff/revision summary metadata when practical.

Potential fields:

- `requirement_diff`;
- `revision_summary`;
- `previous_revision`;
- `current_revision`;
- `changed_fields` if not already present;
- `rag_refresh_reason` if not already present.

Do not break existing clients/tests. Preserve existing response-state behavior.

### 4. Update Recipe Session Alpha UI

Update the demo UI section to show a compact operator-focused change summary.

The UI should show:

- current revision number;
- interpreted requirements;
- changed fields from the latest follow-up;
- revision summary message;
- RAG refreshed vs reused;
- RAG refresh reason or no-refresh reason;
- current draft summary when available;
- citations/support metadata when available.

The UI should remain compact. Do not build a full chat interface.

### 5. Clarify no-refresh behavior

Improve messaging for no-refresh cases such as:

- `thanks`;
- `looks good`;
- `make it shorter`;
- `format this as bullets`;
- repeated finalize.

The UI/API should make clear:

- no material requirements changed;
- RAG was not refreshed;
- the existing draft/citations were reused;
- no new provider generation occurred if that is true.

### 6. Clarify refresh behavior

Improve messaging for refresh cases such as:

- `actually make it no-bake`;
- `use air fryer instead`;
- `make it gluten-free`;
- `no nuts`;
- `use ricotta instead of cream cheese`;
- serving count changes if the current policy treats them as retrieval-relevant.

The UI/API should explain why RAG refreshed in plain language.

### 7. Add tests

Add deterministic tests for:

- requirement diff detects baked -> no-bake;
- requirement diff detects equipment update, such as air fryer;
- requirement diff detects excluded ingredient update, such as no nuts;
- no-refresh messages produce an empty or no-material-change diff;
- revision summary is concise and safe;
- API response includes diff/revision metadata for follow-up messages;
- UI static tests cover the new requirement diff/revision display;
- no raw provider prompts, provider responses, private env values, local paths, or large internal state are exposed.

### 8. Update evals if useful

If practical, extend the recipe-session eval cases to assert revision summary or changed-field behavior for key cases.

Keep evals deterministic, offline, mock-only, and fast.

### 9. Update docs

Update as needed:

- `docs/recipe-session-requirements-architecture.md`;
- `docs/recipe-session-alpha-acceptance-runbook.md`;
- `docs/ai-evals-plan.md`;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md` if relevant.

Create:

```text
outbox/0030G-operator-ux-requirement-diff-and-revision-summaries-results.md
```

The outbox should summarize:

- diff/revision helpers added;
- API response metadata added;
- UI changes;
- no-refresh messaging;
- refresh messaging;
- tests/evals added;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Requirement diff helper exists and is deterministic.
- Revision summary helper exists and is deterministic.
- Recipe-session API responses expose safe diff/revision summary metadata where appropriate.
- Demo UI shows changed fields and revision summary for follow-up messages.
- No-refresh and refresh cases are clearly explained.
- Tests cover meaningful requirement changes and no-material-change cases.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No production storage, persistent memory, auth, paid access, public route exposure, vector DB, embeddings, screenshots, browser automation, raw dataset commits, or generated persistent indexes are added.

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

If direct Windows pytest is run and fails due to the known local `pytest-of-scott` temp ACL issue or because live OpenAI env vars are set, document that separately and rely on Git Bash validation if it passes.

Do not run live OpenAI during normal validation.

## Non-Goals

- no production storage;
- no auth;
- no paid access;
- no public route exposure;
- no Cloudflare changes;
- no database migrations;
- no persistent user memory;
- no vector database;
- no embeddings;
- no Qdrant;
- no pgvector;
- no Redis;
- no live OpenAI calls;
- no full chat UI;
- no browser automation;
- no screenshots;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api evals docs README.md outbox/0030G-operator-ux-requirement-diff-and-revision-summaries-results.md

git commit -m "mailbox: complete task 0030G operator ux requirement diffs"

git pull --rebase origin main

git push origin main
```
