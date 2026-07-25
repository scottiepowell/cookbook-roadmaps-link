# 0033U Save-to-Cookbook Core Adapter Path Decision

## Goal

Resolve the `0033T` native-save blocker by choosing the next architecture path for a true Save-to-Cookbook implementation.

This is an architecture/path decision task. Do not implement a production save path, native save route, authentication bypass, database migration, UI production button, Cloudflare/AWS/GitHub Actions deployment, or live provider integration in this task.

## Context

`0033S` added a local-only UI MVP, but its commit path remains an in-memory local simulation.

`0033Q` proved a disposable local DB/write readiness harness with synthetic data, backup/restore, read-after-write, duplicate/idempotency, rollback, and restoration.

`0033T` attempted the native local save spike and blocked with a precise ownership/session boundary:

- upstream `POST /api/recipe` requires Lucia-authenticated `locals.user`;
- anonymous sidecar requests cannot create recipes;
- the route creates a Prisma `Recipe` row before optional image/upload/embedding behavior;
- there is no dry-run mode or adapter-specific transaction/rollback envelope;
- a safe spike would require either a synthetic authenticated local session/cookie boundary or a core-app adapter/service contract;
- cookies, tokens, session values, real accounts, and unsafe session handling remain prohibited.

The current external Vanilla Cookbook image is not enough for a safe product Save-to-Cookbook implementation unless the core app exposes a reviewed adapter boundary.

## Required Work

### 1. Read current evidence

Read:

```text
outbox/0033T-local-native-save-to-cookbook-spike-results.md
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
outbox/0033R-local-save-to-cookbook-backend-integration-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/local-cookbook-ai-product-integration.md
docker-compose.yml
docker-compose.local.yml
README.md
```

Also inspect any repository docs that explain whether the Vanilla Cookbook app is treated as an external image, upstream dependency, fork, or source-controlled component.

### 2. Define candidate architecture paths

Create a decision note evaluating at least these paths:

```text
Path A: Keep current external image; feature remains local in-memory simulation plus 0033Q harness only.
Path B: Add an explicit core-app adapter to a source-owned/forked Vanilla Cookbook app and build a local custom image.
Path C: Use a reviewed upstream-supported API/plugin hook if one exists or can be contributed upstream.
Path D: Browser/session automation against the existing app.
Path E: Direct sidecar DB writes to Vanilla Cookbook storage.
```

For each path, evaluate:

```text
feasibility
security/ownership model
rollback/transaction story
auth/session risk
maintenance burden
local developer experience
production readiness
how much code must move into the core app
whether it preserves Vanilla Cookbook as canonical recipe owner
whether it avoids direct sidecar DB writes
whether it can support a real Save-to-Cookbook button later
```

Expected posture:

- Path D should be rejected unless there is a very strong, safe reason; browser/session automation is fragile and risks cookie/session handling.
- Path E should remain rejected; direct sidecar DB writes bypass core ownership and validation.
- Path A is acceptable only as a demo/prototype state, not feature-complete Save-to-Cookbook.
- Path B or C is likely required for a real feature.

### 3. Inspect source ownership options without committing external source

If local or repository evidence reveals the upstream Vanilla Cookbook source location, package metadata, license, or repository URL, document it.

Allowed:

```text
read package metadata already present in the local container/image if available
read license/package metadata from existing local files if available
record high-level facts and uncertainty
```

Not allowed:

```text
no vendoring upstream source
no copying external app source into this repo
no committing container source snapshots
no committing licenses or source files copied from the image unless already in this repo and reviewed
no modifying the external app image
no production deployment work
```

If internet is available and current upstream/license facts are needed, use it only for documentation, cite exact source URLs in the note, and do not fetch/vendor source into this repo.

### 4. Recommend the next implementation strategy

Create:

```text
docs/save-to-cookbook-core-adapter-path-decision.md
```

The note must recommend one path.

A likely recommendation is:

```text
Proceed by source-owning or forking the Vanilla Cookbook core app in a separate reviewed task/repo/image, then add a core-owned local adapter endpoint/service that performs review/dry-run/commit inside the app's auth, validation, transaction, and rollback boundary. Keep the current sidecar UI as a candidate producer and local prototype until that core adapter exists.
```

But only recommend this if supported by the evidence.

The recommendation must define the next concrete task, such as:

```text
0033V: prepare source-owned Vanilla Cookbook adapter workspace/custom image plan
```

or:

```text
0033V: implement a local core-app adapter in a forked/source-owned Vanilla Cookbook image
```

Only choose implementation if the ownership/source path is clear enough.

### 5. Update planning docs

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly state:

- current Save-to-Cookbook status is local UI/in-memory plus disposable harness proof;
- true saved recipe in Vanilla Cookbook is blocked by core-app auth/session/adapter boundary;
- production Save-to-Cookbook is not implemented;
- direct sidecar DB writes remain prohibited;
- a core-app adapter/source-owned image or upstream plugin/API path is needed for feature completion.

### 6. Add outbox report

Create:

```text
outbox/0033U-save-to-cookbook-core-adapter-path-decision-results.md
```

Summarize:

```text
paths evaluated
chosen/recommended path
why rejected paths were rejected
source ownership findings
next implementation task recommendation
whether the feature is complete, prototype-only, or blocked
validation results
explicit non-goals
```

## Acceptance Criteria

- A core adapter path decision document exists.
- It uses the actual `0033T` blocker as the basis for the decision.
- It evaluates external image, source-owned/forked core adapter, upstream plugin/API, browser/session automation, and direct DB-write paths.
- It recommends a next concrete task.
- It clearly distinguishes prototype/local simulation from real Save-to-Cookbook completion.
- It does not implement writes, routes, migrations, production integration, or auth/session work.
- It does not commit external source, container snapshots, DB files, local artifacts, secrets, cookies, tokens, prompts, provider outputs, screenshots, traces, uploads, generated indexes, or local env values.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If docs-only, full static/repo validation is enough. Do not run live OpenAI.

## Commit

```bash
git add docs README.md outbox/0033U-save-to-cookbook-core-adapter-path-decision-results.md

git commit -m "docs: decide save to cookbook core adapter path"

git pull --rebase origin main

git push origin main
```
