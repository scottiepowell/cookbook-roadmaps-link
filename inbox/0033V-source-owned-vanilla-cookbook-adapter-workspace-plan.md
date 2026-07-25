# 0033V Source-Owned Vanilla Cookbook Adapter Workspace Plan

## Goal

Prepare the next architecture step after `0033U`: a source-owned or forked Vanilla Cookbook core workspace/custom image plan that can eventually host a core-owned Save-to-Cookbook adapter.

This is a discovery and planning task. Do not vendor, copy, or modify external Vanilla Cookbook source in this repository. Do not implement a save adapter, production save path, native route, migration, UI production button, auth/session work, deployment, or provider integration in this task.

## Context

`0033U` decided that the current external image path cannot complete real Save-to-Cookbook. The current app state is still:

- `0033S` local UI/in-memory simulation;
- `0033Q` disposable DB/write readiness harness;
- no production Save-to-Cookbook;
- no safe native sidecar save path.

The recommended path is a source-owned or separately forked Vanilla Cookbook core workspace/custom image where the core app owns auth, user ownership, validation, transaction, rollback, idempotency, and canonical recipe persistence. A verified upstream plugin/API hook with equivalent guarantees remains preferable if available.

`0033U` also found that this repository treats `jt196/vanilla-cookbook:stable` as an external image and does not contain editable upstream source. Image inspection did not find useful OCI source/license labels or a canonical repository URL. Source ownership, license, and synchronization remain discovery gates.

## Required Work

### 1. Read current decision and integration state

Read:

```text
outbox/0033U-save-to-cookbook-core-adapter-path-decision-results.md
docs/save-to-cookbook-core-adapter-path-decision.md
outbox/0033T-local-native-save-to-cookbook-spike-results.md
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/local-cookbook-ai-product-integration.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/save-to-cookbook-schema-informed-write-plan.md
docker-compose.yml
docker-compose.local.yml
README.md
```

Use actual filenames if they differ.

### 2. Discover upstream source/license provenance

Find the likely upstream source, license, and image build relationship for `jt196/vanilla-cookbook:stable`.

Allowed:

```text
inspect package metadata already present inside the local image/container;
inspect Docker image labels and package files;
search installed/local repo metadata;
use internet research if necessary for public upstream source/license discovery;
record candidate upstream URLs, license, version, image/source relationship, and uncertainty.
```

Not allowed:

```text
no vendoring upstream source;
no copying external source into this repo;
no committing container source snapshots;
no committing downloaded source archives;
no modifying the external image;
no production deployment work;
no secrets, cookies, tokens, sessions, DB files, uploads, or local artifacts.
```

If internet research is used, cite exact public sources in the decision note and clearly separate observed local facts from web-current facts.

### 3. Determine workspace strategy

Evaluate at least these workspace options:

```text
Option 1: separate repository fork/source checkout for Vanilla Cookbook core;
Option 2: Git submodule or subtree in this repo;
Option 3: no source ownership, remain image-only and prototype-only;
Option 4: upstream contribution/plugin/API hook without maintaining a fork;
Option 5: custom local image built from a reviewed source checkout outside this repo.
```

For each option, evaluate:

```text
license/provenance risk;
maintenance and upstream sync;
local developer workflow;
Docker/custom image build path;
auth/session ownership boundary;
adapter implementation location;
testing strategy;
rollback/transaction capability;
production deployment implications;
whether this repo should contain only adapter docs/config versus app source.
```

Expected posture:

- Prefer a separate source-owned/forked workspace or upstream plugin/API hook over copying app source into this repo.
- Avoid submodule/subtree unless license/provenance and maintenance are clearly justified.
- Keep this repo focused on sidecar/product integration unless a separate decision approves a monorepo move.

### 4. Define core-owned adapter contract requirements

Draft the adapter contract that a source-owned Vanilla Cookbook core app would implement later.

The contract should support:

```text
core-authenticated current user ownership;
reviewed import candidate input;
dry-run validation without mutation;
explicit commit after confirmation;
transactional recipe creation;
rollback/cleanup for categories/photos/uploads/embeddings if later enabled;
idempotency key handling;
duplicate detection;
safe status/error envelope;
canonical recipe URL/UID return;
no raw prompts/provider outputs stored as recipe content;
no sidecar-provided userId/session/cookie/auth assertions.
```

It should identify the first local implementation scope:

```text
name/title;
description;
servings text;
deterministic ingredients text;
numbered directions text;
safe source/provenance;
no categories;
no media/uploads;
no embeddings unless explicitly disabled or controlled.
```

### 5. Define custom image/local dev plan

Create a concrete plan for a future custom local image, without implementing it now.

Cover:

```text
where source checkout/fork should live;
how to build a local custom image;
how docker-compose.local.yml would switch from jt196/vanilla-cookbook:stable to the custom image;
how to keep app-only localhost binding;
how to keep cloudflared/AWS/GitHub Actions out of local validation;
how to run migrations safely only in disposable local runtime;
how to run core-app tests plus existing sidecar tests;
how to keep .local DB/uploads ignored;
how to document upstream sync and patch management.
```

### 6. Produce decision/plan docs

Create:

```text
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
```

The plan must include:

```text
upstream/source provenance findings;
license and uncertainty notes;
workspace options evaluated;
recommended workspace strategy;
custom image plan;
core-owned adapter contract sketch;
local development workflow;
testing/validation strategy;
security and rollback boundaries;
next implementation task;
explicit non-goals.
```

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly say:

- current Save-to-Cookbook is prototype-only/in-memory plus disposable harness proof;
- real Save-to-Cookbook requires source-owned/forked core adapter or upstream hook;
- production Save-to-Cookbook is not implemented;
- direct sidecar DB writes and browser/session automation remain rejected;
- no external source is vendored by this task.

### 7. Add outbox report

Create:

```text
outbox/0033V-source-owned-vanilla-cookbook-adapter-workspace-plan-results.md
```

Summarize:

```text
source/license provenance findings;
workspace options evaluated;
recommended strategy;
custom image plan;
core adapter contract requirements;
next implementation task;
docs updated;
validation results;
explicit non-goals.
```

## Acceptance Criteria

- A source-owned/custom-image workspace plan exists.
- Upstream source/license provenance is investigated and documented with uncertainty where needed.
- Workspace options are evaluated and one strategy is recommended.
- Core-owned adapter contract requirements are defined.
- A future custom-image local dev path is planned but not implemented.
- Next implementation task is clearly recommended.
- Current prototype-only status is documented.
- No external source is vendored or committed.
- No save adapter, native route, migration, production integration, auth/session work, public route, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, or live call is implemented.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, cookies, auth tokens, session values, or browser artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

If docs-only, full static/repo validation is enough. Do not run live OpenAI.

## Commit

```bash
git add docs README.md outbox/0033V-source-owned-vanilla-cookbook-adapter-workspace-plan-results.md

git commit -m "docs: plan source-owned cookbook adapter workspace"

git pull --rebase origin main

git push origin main
```
