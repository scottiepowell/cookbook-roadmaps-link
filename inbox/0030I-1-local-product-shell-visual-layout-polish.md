# 0030I-1 Local Product Shell Visual Layout Polish

## Goal

Polish the `/product` local Cookbook AI shell layout so the existing content is readable, balanced, and demo-ready.

This is a focused UI layout/spacing task. The content and integration concept from `0030H` and `0030I` are good, but the current visual layout is cluttered and hard to scan.

## Background

The current `/product` page shows the right ideas:

- Cookbook AI local product title;
- readiness/provider/data status;
- upstream Vanilla Cookbook access;
- AI sidecar workspace access;
- grounded workflow explanation;
- start/reset guidance;
- mock/offline and demo-only boundaries.

However, visual review of the local page shows layout issues:

- cards are too cramped;
- three-column content does not fit cleanly at the current viewport;
- action buttons overflow horizontally and overlap or extend beyond their cards;
- spacing and alignment make the page difficult to read;
- card headings and body copy are not visually balanced;
- the page feels more like raw blocks than a clean product landing shell.

Fix the layout without changing the product architecture.

## Scope

Improve the `/product` visual presentation only.

Likely files:

- `ai-api/app/static/product.html`
- `ai-api/app/static/product.css`
- `ai-api/app/static/product.js` if needed
- `ai-api/tests/test_demo_ui.py` or product-shell tests
- `scripts/demo-ai-mock.ps1` if smoke checks need updated markers
- `docs/local-product-acceptance-checklist.md`
- `docs/local-cookbook-ai-product-integration.md`
- `outbox/0030I-1-local-product-shell-visual-layout-polish-results.md`

If the product shell uses different filenames, inspect the actual `/product` route/static files and update those.

## Required Work

### 1. Review the current product shell layout

Inspect the `/product` markup and CSS.

Confirm the current page has these layout problems:

- horizontal overflow or action button overflow;
- cards too narrow for their content;
- excessive visual crowding;
- inconsistent alignment;
- weak spacing hierarchy;
- poor scanability.

### 2. Redesign the layout for readability

Keep the same product content, but improve placement.

Preferred layout:

```text
Header
  - small eyebrow: Local integrated product
  - title: Cookbook AI
  - short description

Readiness card
  - full-width or prominent card
  - concise readiness summary

Primary action cards
  - responsive two-column or stacked layout, not cramped three-column
  - Cookbook card
  - AI Recipe Creator card
  - Grounded workflows card if still useful

Guidance card
  - full-width start/reset guidance
```

Use CSS grid or flex in a way that avoids overflow.

The layout should work cleanly at common desktop widths around 1366-1600px and should gracefully stack on smaller widths.

### 3. Fix button placement

Action buttons must stay inside their cards.

Do not allow buttons to:

- overlap adjacent cards;
- extend beyond the viewport;
- cover text;
- detach visually from their card;
- create horizontal scrolling.

Prefer card actions at the bottom of each card with consistent spacing.

Example visual behavior:

```text
[ Card title ]
[ Body copy  ]
[ Metadata   ]

[ Open Cookbook ]
```

or:

```text
[ Card title        ]
[ Body copy         ]
[ Open Cookbook     ]
```

### 4. Improve visual hierarchy

Improve scanability with:

- clearer max-width container;
- consistent card padding;
- consistent gaps between cards;
- readable line lengths;
- balanced heading/body sizes;
- subtle section grouping;
- enough whitespace between readiness, actions, and guidance.

Do not over-design. Keep it clean, simple, and portfolio-demo appropriate.

### 5. Preserve content and safety boundaries

Do not remove important safety content.

The product shell must still communicate:

- Vanilla Cookbook is the upstream local app;
- AI workflows are in the sidecar;
- mock/offline is default;
- fixture recovery guidance;
- Recipe Session finalize is demo-only;
- no production write-back.

The shell must not expose:

- secrets;
- `.env` values;
- raw provider prompts;
- raw provider responses;
- local filesystem paths;
- raw dataset content.

### 6. Improve responsive behavior

Add or update responsive CSS so the layout:

- has no horizontal scroll at normal desktop widths;
- stacks cleanly on narrower screens;
- keeps buttons and text readable;
- preserves card order logically.

Suggested breakpoint behavior:

- wide desktop: two-column action layout or balanced card grid;
- medium width: two columns or stacked depending on available width;
- narrow width: one column.

### 7. Add or update tests

Add deterministic tests for:

- product shell still renders;
- product shell still contains Cookbook and AI workspace actions;
- product shell contains readiness and recovery guidance;
- product shell does not include unsafe strings;
- CSS includes responsive/layout rules that prevent obvious overflow, such as `box-sizing`, `max-width`, `grid-template-columns`, and a media query or equivalent responsive rule;
- existing `/demo` route remains available.

If tests already cover some of this, extend them rather than duplicating.

### 8. Update docs/outbox

Update docs only if wording changed or if the acceptance checklist should mention the visual inspection standard.

Create:

```text
outbox/0030I-1-local-product-shell-visual-layout-polish-results.md
```

The outbox should summarize:

- visual issue addressed;
- layout changes;
- responsive behavior;
- tests updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- `/product` looks clean and readable at normal desktop width.
- Product cards do not collide or overlap.
- Action buttons stay inside their cards.
- No horizontal overflow is introduced.
- Readiness, actions, and guidance have clear visual separation.
- Content remains accurate and safe.
- `/product/cookbook`, `/product/ai`, and `/demo` behavior remains unchanged.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No AWS/platform work is implemented.
- No upstream Vanilla Cookbook vendoring or UI rewrite is added.
- No production write-back, production storage, public route exposure, auth, payment, provider-routing, secondary provider runtime, vector DB, embeddings, raw dataset, screenshot, browser automation, generated persistent index, or disk cache work is added.

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

Do not run live OpenAI during normal validation.

If direct Windows pytest fails due to the known `pytest-of-scott` temp ACL issue, document that separately and rely on Git Bash validation if it passes.

## Non-Goals

- no AWS resource creation;
- no Terraform;
- no CDK;
- no CloudFormation;
- no DNS or Cloudflare changes;
- no production deployment;
- no production auth;
- no payment implementation;
- no public route exposure;
- no provider-routing changes;
- no secondary-provider runtime;
- no live OpenAI calls;
- no vector database;
- no embeddings;
- no upstream Vanilla Cookbook vendoring;
- no full upstream UI rewrite;
- no production database migrations;
- no persistent production memory;
- no screenshots or browser automation;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api docs scripts outbox/0030I-1-local-product-shell-visual-layout-polish-results.md

git commit -m "mailbox: complete task 0030I-1 local product shell visual polish"

git pull --rebase origin main

git push origin main
```
