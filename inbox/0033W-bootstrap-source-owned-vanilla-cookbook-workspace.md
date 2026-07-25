# 0033W Bootstrap Source-Owned Vanilla Cookbook Workspace

## Goal

Bootstrap the source-owned/forked Vanilla Cookbook workspace and custom local image path recommended by `0033V`, while preserving strict provenance, license, local-only, and no-production boundaries.

This is the first task that may create or configure a separate source-owned Vanilla Cookbook workspace outside this sidecar repository. It must not vendor upstream source into this repository. It must complete provenance/license review before any fork/source checkout/custom image work is treated as accepted.

## Context

`0033V` decided that real Save-to-Cookbook cannot be completed with only the external `jt196/vanilla-cookbook:stable` image. The current feature remains prototype-only: `0033S` provides the local sidecar/in-memory simulation, and `0033Q` provides disposable DB/write readiness evidence. No normal product flow saves a recipe in Vanilla Cookbook.

`0033V` recommended a separate source-owned/forked Vanilla Cookbook core workspace with a distinct local custom image, while preferring an upstream plugin/API hook if one exists with equivalent auth, ownership, validation, idempotency, transaction, and rollback guarantees.

## Required Work

### 1. Read the current decision records

Read:

```text
outbox/0033V-source-owned-vanilla-cookbook-adapter-workspace-plan-results.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
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
.gitignore
```

Use actual filenames if they differ.

### 2. Complete provenance and license review before source ownership

Verify the likely upstream Vanilla Cookbook source, license, submodules, and Docker image relationship.

Allowed:

```text
inspect current local image/container metadata
inspect public upstream repository metadata
inspect upstream LICENSE and submodule/license files
inspect public installation/build documentation
record exact upstream URL, commit/tag/branch, license facts, submodule facts, Docker image/build facts, and uncertainty
```

Requirements:

- Use web/current public sources if internet is available because upstream/license facts may have changed.
- Cite exact source URLs in the new documentation.
- Clearly separate observed local facts, web-current facts, and uncertainty.
- If license/submodule redistribution terms are unclear or incompatible, stop before custom image work and document the blocker.

Not allowed:

```text
no vendoring upstream source into this repo
no committing downloaded source archives
no committing copied container source snapshots
no committing upstream source files into this repo
no production deployment work
no secrets/cookies/tokens/session values/local DBs/uploads/artifacts
```

### 3. Establish a separate source-owned workspace only if gates pass

If provenance/license gates pass, bootstrap a separate local workspace outside this repository for the source-owned/forked Vanilla Cookbook core app.

Expected location pattern may be something like:

```text
C:\Users\scott\projects\vanilla-cookbook-core
/home/scott/projects/vanilla-cookbook-core
```

Choose a location that is clearly outside `C:\Users\scott\cookbook-roadmaps-link` / this repository.

Allowed:

- create or document a separate local checkout/fork workspace;
- pin an upstream commit/tag/branch;
- record the workspace path generically in docs, avoiding absolute local path exposure where possible;
- create a small repo-local helper script only if it does not vendor source and does not require secrets;
- create docs explaining how to clone/build the separate workspace.

Not allowed:

- do not copy the source tree into this sidecar repo;
- do not add the upstream as a submodule/subtree here;
- do not commit external source, license copies, source snapshots, or archives here;
- do not commit local workspace absolute paths, secrets, tokens, cookies, DBs, uploads, or generated build artifacts.

If creating the separate workspace is not possible in this environment, document exact manual steps and stop before implementation.

### 4. Build or plan a distinct local custom image

If the separate source workspace exists and build prerequisites are available, attempt a local-only custom image build from the separate workspace.

Requirements:

- use a distinct image tag, for example `local/vanilla-cookbook-adapter:0033w`;
- do not retag or mutate `jt196/vanilla-cookbook:stable`;
- do not push the image anywhere;
- do not use GitHub Actions, AWS, Cloudflare, tunnels, or production secrets;
- keep the image local-only;
- record safe build status without committing build artifacts.

If the build fails due missing prerequisites, license gate, missing source, or upstream build issues, document the precise blocker and recovery steps.

### 5. Add sidecar-repo configuration for optional custom image only if safe

If a custom local image exists or the plan is clear enough, add a small optional local configuration path in this repository so `docker-compose.local.yml` can select a custom image without changing the default external image workflow.

Acceptable approaches:

```text
COMPOSE env var such as VANILLA_COOKBOOK_IMAGE
local-only compose override documentation
script parameter such as -CookbookImage
```

Requirements:

- default remains `jt196/vanilla-cookbook:stable`;
- custom image path is opt-in only;
- app remains bound to `127.0.0.1:3000`;
- project remains `cookbook-local`;
- no `cloudflared` starts;
- no AWS/GitHub Actions/Cloudflare/production config is required;
- `.local/vanilla-cookbook/db` and uploads remain ignored.

Add tests/docs for config rendering if code/config changes are made.

### 6. Define the first core-owned adapter implementation boundary

Do not implement the adapter unless the task can safely operate inside the separate source workspace and still commit only sidecar docs/config/outbox here.

At minimum, document the first core adapter implementation target:

```text
core-authenticated dry-run endpoint/service
no mutation during dry-run
reviewed candidate input
ownership derived from core session/user
idempotency key accepted and checked
duplicate fingerprint checked
safe field errors/warnings
canonical mapping for name, description, servings, ingredients, directions, source, notes
no categories, media/uploads, remote image fetches, or embeddings in first scope
commit endpoint deferred until dry-run is proven
```

If the separate source workspace is usable and changes can be made there, do not commit those external-workspace changes to this sidecar repo unless the workflow explicitly supports multiple repos. Instead, document the external workspace branch/commit/status in the outbox.

### 7. Update documentation

Create:

```text
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
```

The document must cover:

```text
provenance and license review results
upstream source URL and exact pin/uncertainty
submodule/license findings
separate workspace location strategy
whether a local checkout/fork was created
whether a custom local image was built
custom image tag and safe local usage
optional compose/script configuration
first core adapter implementation boundary
manual recovery steps if blocked
next recommended task
explicit non-goals
```

Update as appropriate:

```text
README.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly say:

- current Save-to-Cookbook remains prototype-only until a core adapter exists;
- upstream/source/license provenance gate status;
- whether a source-owned workspace/custom image is ready or blocked;
- production Save-to-Cookbook remains not implemented;
- direct sidecar DB writes and browser/session automation remain rejected;
- no external source is vendored into this repo.

### 8. Add outbox report

Create:

```text
outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md
```

Summarize:

```text
provenance/license review results
workspace bootstrap result
custom image build result or blocker
sidecar compose/script config changes
core adapter boundary defined
next task recommendation
validation results
explicit non-goals
```

## Acceptance Criteria

- Provenance and license review is completed or precisely blocked.
- No upstream source is vendored/copied/committed into this repository.
- A separate source-owned workspace is created or precise manual bootstrap steps are documented.
- A custom local image is built or the precise blocker/recovery is documented.
- Any optional sidecar compose/script config remains local-only and defaults to the external image.
- The first core-owned dry-run adapter boundary is defined.
- Current prototype-only status is documented.
- No production Save-to-Cookbook, public route, migration, auth/session work, production deployment, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, or live call is implemented.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, cookies, auth tokens, session values, browser artifacts, source archives, external source files, or container source snapshots are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

If config/scripts change, run the relevant focused tests and repository test suite.

Do not run live OpenAI.

## Commit

```bash
git add docker-compose*.yml scripts docs README.md outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md

git commit -m "dev: bootstrap source-owned cookbook workspace plan"

git pull --rebase origin main

git push origin main
```
