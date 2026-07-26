# 0034H — Local UI Real-Save Wiring

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not implement production authentication.
Do not implement real Google login.
Do not call Google, Microsoft, OpenAI, OAuth, storage providers, or live external providers.
Do not request Google Drive or storage scopes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or production deployment.
Do not inspect or modify production data.
Do not bypass production auth.
Do not create, export, print, persist, or commit cookies, auth tokens, sessions, OAuth codes, refresh tokens, access tokens, ID tokens, client secrets, real user credentials, browser state, or real account data.
Do not use browser/session automation.
Do not add direct sidecar database writes.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, sessions, OAuth state, or real profile data.

## Goal

Wire the existing local importer review UI to the disabled-by-default sidecar persistent save transport proven in `0034G`, while preserving the core-owned identity boundary.

This task should let a local operator see a reviewed AI draft in the sidecar UI, explicitly confirm a **local/dev-only real save**, call the `0034G` core-owned persistent route through the sidecar transport, and render only safe save status/UID/idempotency/canonical-link information.

This is still not production Save-to-Cookbook and not real Google login. It may mutate only the disposable local `cookbook-local` runtime under explicit local approval and backup/restore behavior already proven by `0034G`.

## Context

`0034G` proved:

```text
core-owned persistent synthetic AuthUser
core-owned ownership derivation
core dry-run -> commit -> read-after-write
replay/conflict behavior
duplicate review behavior
failure/rollback verification
DB/uploads backup and restore
safe HTTP 200 verification
sidecar transport function send_core_local_persistent_commit
```

Remaining blocker from `0034G`: the normal sidecar UI still uses the `0033S` in-memory prototype and does not call the persistent transport.

## Read first

```text
outbox/0034G-core-owned-local-persistent-user-auth-transport-results.md
docs/core-owned-local-persistent-user-auth-transport.md
outbox/0034F-sidecar-to-core-local-real-save-transport-results.md
docs/sidecar-to-core-local-real-save-transport.md
outbox/0034E-google-first-core-oidc-local-auth-spike-results.md
docs/google-first-core-oidc-local-auth-spike.md
outbox/0034C-core-owned-dev-only-synthetic-auth-fixture-results.md
docs/core-owned-dev-only-synthetic-auth-fixture.md
outbox/0033S-local-importer-review-ui-results.md
ai-api/app/cookbook_core_transport.py
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
ai-api/app/static/demo.js
ai-api/app/main.py
ai-api/tests/test_demo_ui.py
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

Inspect the external Vanilla Cookbook workspace only if needed to confirm route names or safe response fields. Keep all external source outside this sidecar repository.

## Implementation scope

In the sidecar repository, implement the smallest local/dev-only UI wiring around the existing persistent transport.

Acceptable shape:

```text
local-only FastAPI route or service wrapper that calls send_core_local_persistent_commit
review-panel control in ai-api/app/static/demo.js
safe status rendering and tests
```

The UI/save path must:

```text
remain disabled by default;
require explicit local enablement;
require explicit user/operator confirmation per save;
require the loopback core target such as http://127.0.0.1:3000;
require cookbook-local and the local/vanilla-cookbook-adapter:0034g image marker or an explicitly allowed local adapter marker;
refuse production, exposed, tunnel, Cloudflare, AWS, GitHub Actions, and CI contexts;
send only reviewed recipe candidate data, idempotency key, contract version, and local approval;
never send userId, cookie, session, token, OAuth code, provider grant, or storage grant;
call only the existing sidecar transport, not the Cookbook DB;
show only safe status/UID/idempotency/duplicate/conflict/rollback/canonical-link fields;
render safe unavailable/error messages when disabled or blocked;
keep the existing in-memory prototype available when local real-save is disabled;
label the feature clearly as local/dev-only and not production.
```

The UI must not imply that the saved recipe can be browser-opened in Vanilla Cookbook under a real user session unless that is actually proven without cookies/tokens/sessions or browser automation. If UI observation in Vanilla Cookbook requires real session credentials, show the safe core read-after-write result and document the limitation.

Do not add persistent provider auth, Google login, session cookies, migrations, production routes, or Drive/storage behavior.

## Tests

Add focused sidecar tests for:

```text
UI/route disabled by default;
missing explicit confirmation refuses before transport call;
production/exposed/non-loopback/tunnel/CI guard refusal;
core target and image marker requirements;
reviewed candidate payload only;
identity/session/token/provider/storage fields are never sent;
success envelope rendering;
replay/conflict/duplicate/rollback status rendering;
safe unavailable/error rendering;
leakage checks for prompts/provider output/secrets/stack traces/paths/tokens/sessions;
existing in-memory review prototype still works when local real-save is disabled;
normal validation remains mock/offline and does not require Docker or live providers.
```

Optional local verification, only if the UI and transport are safely implemented:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034g

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

# Run only the approved local/dev sidecar UI or API save verification with explicit local approval.
# Do not export, print, or save cookies/tokens/sessions.
# Do not call Google/OAuth/OpenAI/storage providers.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

## Sidecar repository updates

Create:

```text
docs/local-ui-real-save-wiring.md
outbox/0034H-local-ui-real-save-wiring-results.md
```

Update as appropriate:

```text
README.md
docs/core-owned-local-persistent-user-auth-transport.md
docs/sidecar-to-core-local-real-save-transport.md
docs/sidecar-real-save-local-wiring-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The outbox must summarize:

```text
UI wiring implementation status;
route/service changes;
transport settings and guard behavior;
safe payload behavior;
safe rendering behavior;
local verification result if run;
whether saved recipe can be observed in Vanilla Cookbook UI or why not;
remaining blockers before production Save-to-Cookbook;
remaining blockers before real Google login;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
Local/dev-only sidecar UI real-save wiring is implemented or precisely blocked.
No external source is committed into this sidecar repository.
No production auth or production Save-to-Cookbook is implemented.
No real Google/OAuth/provider/storage call is made.
No cookie/token/session/OAuth code/real credential/browser state is created/exported/printed/committed.
Sidecar sends no userId/session/cookie/token/provider/storage grant.
Core owns synthetic AuthUser and commit authorization.
UI clearly labels local/dev-only status and production unsupported status.
Normal sidecar validation remains mock/offline.
Direct sidecar DB writes and browser/session automation remain rejected.
Docs/outbox record whether local saved recipe UI observation is possible without credentials.
```

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet

& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Do not run live OpenAI, Google, Microsoft, OAuth, or storage calls.

Commit sidecar changes:

```bash
git add ai-api scripts docs README.md outbox/0034H-local-ui-real-save-wiring-results.md

git commit -m "feat: wire local ui real save"

git pull --rebase origin main

git push origin main
```
