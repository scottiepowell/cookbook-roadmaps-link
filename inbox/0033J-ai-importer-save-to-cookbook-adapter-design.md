# 0033J AI Importer Save-To-Cookbook Adapter Design

## Goal

Design the safe path for adding a **Save to Cookbook** action after the AI recipe importer creates a draft, so an accepted AI-generated recipe can be imported into the Vanilla Cookbook application.

This is an adapter/design task first. Do not directly write to the Vanilla Cookbook database or implement production write-back until the schema, ownership boundary, validation rules, rollback plan, and user confirmation flow are documented and tested.

## Context

Manual live testing on 2026-07-24 showed the AI importer can successfully create usable recipe drafts using `openai` / `gpt-5.4-nano` with a larger local live cap.

The next important product step is to let the user save an accepted AI importer draft into the Vanilla Cookbook app. This likely belongs to the plugin/adapter work rather than letting the AI sidecar directly mutate Cookbook-owned storage.

Relevant prior architecture:

- The current Vanilla Cookbook app is treated as the canonical recipe owner.
- The AI sidecar currently creates validated draft recipe JSON and does not write to production Cookbook storage.
- `0031C` defined a future adapter boundary between the core Cookbook app and the RAG/AI sidecar.
- `0033A` found that the product still feels split between Vanilla Cookbook and the AI demo workspace.

## Required Work

### 1. Read current architecture and importer docs

Read:

```text
docs/cookbook-ai-plugin-adapter-architecture-adr.md
docs/local-cookbook-ai-product-integration.md
docs/ai-sidecar-architecture.md
docs/manual-product-integration-usability-validation.md
outbox/0033A-manual-product-integration-usability-validation-results.md
docs/ai-live-demo-runbook.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Also inspect importer code, schemas, tests, and any existing recipe-reader/schema notes:

```text
ai-api/app/**import*
ai-api/app/**recipe*
ai-api/tests/**import*
ai-api/tests/**recipe*
docs/ai-schema-notes.md
```

Use actual filenames if globbing differs.

### 2. Produce a design note

Create:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
```

The design must cover:

- problem statement;
- why direct AI sidecar DB write-back is risky;
- preferred adapter boundary for saving imported recipes;
- user flow from AI draft -> review/edit -> save -> Cookbook recipe appears;
- draft validation requirements before save;
- fields to map from AI draft to Vanilla Cookbook recipe fields;
- unknown schema fields and discovery requirements;
- duplicate detection strategy;
- source/provenance handling;
- user confirmation and editability;
- rollback/delete behavior if a save fails midway;
- local fixture strategy;
- production data safety requirements;
- tests required before any implementation;
- phased implementation plan;
- explicit non-goals.

### 3. Define candidate implementation phases

Use a phased approach such as:

```text
Phase 0: design only and schema review
Phase 1: local fixture adapter contract with no Vanilla DB writes
Phase 2: dry-run save endpoint returning mapped payload and validation errors
Phase 3: local disposable Vanilla Cookbook DB write test with backup/rollback
Phase 4: UI Save to Cookbook button enabled only for disposable/local target
Phase 5: reviewed production adapter path or upstream API integration if available
```

### 4. Define candidate API/UI shape

Sketch endpoints and UI concepts, but do not implement unless explicitly approved later.

Possible API sketches:

```text
POST /adapter/recipes/import-candidate
POST /adapter/recipes/import-candidate/dry-run
POST /adapter/recipes/import-candidate/{id}/commit
GET  /adapter/recipes/{id}
```

Possible UI flow:

```text
Run AI importer
Review structured draft
Edit draft fields
Click Save to Cookbook
See validation/dry-run result
Confirm save
Open saved recipe in Cookbook
```

### 5. Define safety gates

The design must require:

- no production write-back without explicit approval;
- disposable/local DB test before any real Cookbook DB mutation;
- backup or restore point before write-back;
- schema detection/compatibility check;
- strict draft validation;
- user confirmation;
- idempotency/duplicate protection;
- safe error messages;
- no raw provider output stored as canonical recipe data;
- no prompts, provider bodies, secrets, local paths, or tokens stored or exposed.

### 6. Update planning docs

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

### 7. Add outbox report

Create:

```text
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
```

Summarize:

- design created;
- adapter/save direction;
- draft review/edit/save flow;
- schema/write-back risks;
- safety gates;
- phased implementation plan;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Save-to-Cookbook adapter design exists.
- Design keeps Vanilla Cookbook as canonical recipe owner.
- Design avoids direct production DB writes in this task.
- Design defines review/edit/confirm flow before save.
- Design defines schema discovery and field mapping needs.
- Design defines safety gates, rollback expectations, and tests.
- Design links the work to the plugin/adapter boundary from `0031C`.
- No runtime save button, write endpoint, DB mutation, production integration, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, or local env values are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If this remains docs-only, full static/repo validation is enough. Do not run live OpenAI during normal validation.

## Commit

```bash
git add docs README.md outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
git commit -m "docs: add ai importer save to cookbook adapter design"
git pull --rebase origin main
git push origin main
```
