# 0034B: Sidecar Real-Save Local Wiring Plan

Status: planned.

Goal: define the next safe bridge from the sidecar UI/in-memory Save-to-Cookbook MVP to a real local-only save through the source-owned Vanilla Cookbook core adapter, using the evidence from `0034A` without adding production save support.

This is a planning/gate task first. Do not implement production Save-to-Cookbook, public routes, migrations, auth bypasses, browser/session automation, direct sidecar DB writes, AWS/GitHub Actions/Cloudflare work, provider routing changes, QMD, analytics, ads, payment, SSO/BYOS, or live OpenAI calls.

Context:

- `0033S` added a local sidecar UI and in-memory commit simulation.
- `0033Y` added the authenticated core dry-run route in the external Vanilla Cookbook workspace.
- `0033Z` added the authenticated core commit route/service in the external workspace.
- `0034A` proved the core commit service with a synthetic `AuthUser`, real SQLite persistence, read-after-write, replay/conflict, duplicate blocking, rollback, and backup/restore.
- `0034A` did not verify browser/HTTP session runtime behavior because exporting session credentials, cookies, tokens, or real credentials remains prohibited.
- Production Save-to-Cookbook remains unimplemented.

Read first:

```text
outbox/0034A-core-owned-local-auth-commit-verification-results.md
docs/core-owned-local-auth-commit-verification.md
outbox/0033Z-core-owned-local-commit-adapter-results.md
docs/core-owned-local-commit-adapter.md
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/save-to-cookbook-schema-informed-write-plan.md
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
```

Create:

```text
docs/sidecar-real-save-local-wiring-plan.md
```

The plan must cover:

```text
current completed evidence
remaining blocker between sidecar UI and real core save
why session/cookie export remains prohibited
safe options for local-only route verification
safe options for in-process core route fixtures
how sidecar UI could call a real core-owned adapter without owning auth
how disposable runtime backup/restore must wrap any real local UI save test
required custom image tag expectations
required local-only target and loopback guardrails
required operator approval gates
dry-run-before-commit sequence
rollback and cleanup expectations
duplicate/idempotency behavior expected by the UI
safe user-facing messages
safe operator/debug messages
what must remain disabled in production/exposed deployments
next implementation task recommendation
explicit non-goals
```

Evaluate at least these options:

```text
Option A: Keep sidecar UI in-memory only and rely on core service tests/harness evidence.
Option B: Add a core-owned local test route/fixture that performs dry-run/commit with synthetic in-process auth only when an explicit local dev flag is enabled.
Option C: Add a sidecar-to-core local adapter client that calls authenticated routes only after a safe local auth fixture exists.
Option D: Export or capture browser session cookies/tokens for route testing.
Option E: Direct sidecar DB writes.
```

Expected posture:

- Option D should remain rejected.
- Option E should remain rejected.
- Option A is acceptable as current prototype state but not feature-complete.
- Option B is likely the safest next implementation step if it can be kept inside the source-owned core app, dev-only, and explicitly disabled by default.
- Option C should wait until Option B or an equivalent safe auth fixture exists.

Define the next concrete implementation task. A likely recommendation is:

```text
0034C: implement a core-owned local dev-only adapter verification fixture in the external Vanilla Cookbook workspace, disabled by default, with synthetic in-process AuthUser, disposable DB backup/restore, dry-run-before-commit, and no session/cookie/token export.
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

Create:

```text
outbox/0034B-sidecar-real-save-local-wiring-plan-results.md
```

The outbox must summarize:

```text
plan created
options evaluated
recommended local-only wiring strategy
rejected options
remaining production blockers
next implementation task
validation results
explicit non-goals
```

Acceptance criteria:

- A sidecar real-save local wiring plan exists.
- The plan uses `0034A` evidence accurately.
- The plan clearly explains why route-level session verification remains blocked without a safe core-owned fixture.
- The plan rejects cookie/session/token export and direct sidecar DB writes.
- The plan recommends a concrete next implementation task.
- No production save, public route, migration, auth bypass, browser/session automation, direct sidecar DB write, AWS/GitHub Actions/Cloudflare work, QMD, analytics, ads, payment, SSO/BYOS, provider routing, live call, secret, prompt, provider output, screenshot, trace, raw dataset, generated index, local env value, DB, upload, row dump, cookie, token, session, or browser artifact is committed.

Validation:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

Commit:

```bash
git add docs README.md outbox/0034B-sidecar-real-save-local-wiring-plan-results.md

git commit -m "docs: plan sidecar real save local wiring"

git pull --rebase origin main

git push origin main
```
