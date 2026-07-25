# Local Cookbook AI Product Integration

## Decision

The local integration uses a sidecar-served product shell. Open
`http://127.0.0.1:8000/product` first; it presents Vanilla Cookbook and the AI
workflows as one local product while preserving their ownership boundary.

| Route | Role |
| --- | --- |
| `/product` | Local entry point, safe readiness, and operator guidance. |
| `/product/cookbook` | Redirect to the configured external Vanilla Cookbook target; local default is port 3000. |
| `/product/ai` | Redirect to the existing sidecar AI workspace at `/demo`. |
| `/demo` | Existing AI Recipe Creator, Recipe Session, Ask, Dataset, and Meal Plan UI. |

Vanilla Cookbook runs from the `jt196/vanilla-cookbook:stable` external image
and its editable frontend source is not in this repository. The shell is
therefore intentionally a link integration rather than an upstream UI rewrite
or vendored copy.

## Cookbook handoff targets

The sidecar uses the non-secret `COOKBOOK_TARGET_URL` setting for the
`/product/cookbook` redirect. If it is unset or invalid, the safe local default
is `http://127.0.0.1:3000/`, which is the Docker Compose Vanilla Cookbook
container. An exposed deployment can set the same setting to its reachable
Cookbook URL, such as `https://cookbook.roadmaps.link/`; the AI sidecar does not
guess a public hostname or proxy the upstream application.

The product page explains this handoff and recovery path. If the local target
is unavailable, start Docker Compose and refresh `/product`, or use the
configured exposed Cookbook URL when operating an exposed deployment. The AI
workspace remains at `/demo`, and `/product/ai` continues to redirect there.

## Local operation

### Two-terminal local runtime

Docker Desktop must be running before the local Vanilla Cookbook command.
Verify the daemon with `docker info`; the scripts fail clearly if the Docker
daemon is unavailable.

Vanilla Cookbook is available locally through the dedicated app-only Compose
file, without AWS, Cloudflare Tunnel, GitHub Actions, or production secrets:

```powershell
# Terminal 1: start local Vanilla Cookbook only
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

# Optional readiness check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
```

In a second terminal, start the AI sidecar in deterministic mock mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

The local surfaces are:

| Surface | URL |
| --- | --- |
| Vanilla Cookbook Docker runtime | `http://127.0.0.1:3000/` |
| AI product shell | `http://127.0.0.1:8000/product` |
| AI workspace | `http://127.0.0.1:8000/demo` |

Stop only the local Cookbook runtime with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

The local Compose project is `cookbook-local`, binds only to localhost, and
stores disposable database/uploads under ignored
`.local/vanilla-cookbook/`. The check reports container and port state and
attempts an HTTP request; an image may be running before its page is ready.

This runtime is the prerequisite for future `0033J` adapter schema discovery
and disposable write/rollback tests. It does not implement Save to Cookbook or
write to production data.

The local development machine was also checked for prior Coder/Vanilla
Cookbook Docker assets. Only a generic `coder-docker-template` workspace
template and unrelated VS Code server caches were found; no Vanilla Cookbook
image, Compose file, or non-secret app-specific pattern was available to
reuse. The generic template was treated as read-only and was not copied.

`scripts\start-ai-demo-local.ps1` generates a temporary local SQLite/database
fixture and small dataset fixture, starts the sidecar on port 8000, and prints
the product URL. Start Docker Compose separately when the upstream Cookbook
container is needed on port 3000. If product readiness reports missing saved
recipes or dataset data, restart the seed/start script; generated artifacts
remain ignored.

For a live local profile, set both `AI_MODEL=gpt-5.4-nano` and
`OPENAI_MODEL=gpt-5.4-nano`; this product supports no other live model. An
explicit `-Provider mock` override forces `OPENAI_ENABLE_LIVE_TESTS=false` and
`AI_MODEL=mock-basic` in the child process so validation cannot inherit a
usable live setting.

The launcher automatically imports ignored local `.env` values only when the
corresponding process variable is absent. A valid local live profile uses
`AI_PROVIDER=openai`, `OPENAI_ENABLE_LIVE_TESTS=true`,
`OPENAI_MODEL=gpt-5.4-nano`, a 500–1000 output-token cap for local live mode,
with 500 recommended and 1000 as the ceiling, a 1–25 cent budget, and
an `OPENAI_API_KEY`. The key is injected into the child Uvicorn process
environment only; it is never placed in browser storage, static JavaScript,
URLs, or request bodies. `-WriteMissingLiveDefaults` writes safe non-secret
defaults to ignored `.env` and deliberately never writes a key.

The shell reads only `/demo/readiness`, exposing provider mode/model and data
availability. It does not show environment values, paths, prompts, provider
responses, credentials, or raw dataset content.

The AI workspace carries its browser-selected mode on each provider-backed
request. `Mock offline` requests `mock/mock-basic`; `Live OpenAI` requests
only `openai/gpt-5.4-nano` and remains unavailable unless the server has the
existing explicit live opt-in, key, and budget configuration. This is
request-scoped routing, not a browser mutation of the process-wide provider.

Use the [Local Product Acceptance Checklist](local-product-acceptance-checklist.md)
for the go/no-go local demo flow before AWS/platform planning resumes.
For repeatable browser-facing troubleshooting, see
[Playwright UI Troubleshooting](playwright-ui-troubleshooting.md). It is
optional/local and uses a mock sidecar by default.

For a controlled live importer 503, use the approval-gated
`scripts/diagnose-live-importer.ps1` preflight. It verifies the ignored server
configuration, allows at most one `gpt-5.4-nano` importer call, and emits only
safe category/guidance metadata; it never exposes provider internals.

## Local Save-to-Cookbook UI MVP

The importer in `/demo` now has a local-only review panel. A returned recipe is
marked as an unsaved AI draft; the operator may review the title/description,
run the local dry-run, inspect safe status/errors/warnings, and explicitly
confirm a local commit attempt. The panel never claims production save support.

The routes are internal and disabled by default:

```text
POST /adapter/recipes/import-candidate/dry-run
POST /adapter/recipes/import-candidate/local-commit
```

For an intentional mock/local UI exercise, restart the sidecar with these
non-secret settings and keep `COOKBOOK_TARGET_URL` loopback-only:

```text
AI_LOCAL_SAVE_ENABLED=true
AI_LOCAL_SAVE_APPROVED=true
AI_LOCAL_COOKBOOK_RUNTIME_VERIFIED=true
COOKBOOK_TARGET_URL=http://127.0.0.1:3000/
```

The commit route exercises the 0033R in-memory local service only; it does not
call the upstream native API or mutate SQLite/uploads. The 0033Q readiness
harness remains the sole approved disposable DB/write proof. Exposed targets,
non-loopback clients, tunnels, and production settings remain unavailable.

The 0033T native-save spike reviewed the upstream route but did not wire it:
Lucia authentication/session ownership and post-create image/embedding side
effects are not a safe sidecar contract under the current boundaries. The UI
therefore remains an in-memory local simulation; no browser session, cookie, or
auth token is created or handled.

The 0033U path decision recommends a source-owned/forked core workspace and
custom local image, or a reviewed upstream plugin/API hook if one can provide
the same ownership and transaction guarantees. Until then, the local UI is a
prototype and the 0033Q harness is disposable evidence only. Production save
support is not implemented. The 0033V workspace plan
([source-owned Vanilla Cookbook adapter workspace plan](source-owned-vanilla-cookbook-adapter-workspace-plan.md))
sets the provenance, license, custom-image, and core-adapter gates for the
0033W follow-up.
0033W has now bootstrapped a separate recursive source checkout and the
local-only `local/vanilla-cookbook-adapter:0033w` image. The default local
Compose path still uses `jt196/vanilla-cookbook:stable`; use the opt-in
`-CookbookImage` selector only with the approved local image namespace.
0033X adds a core-owned no-mutation dry-run service and 0033Y adds the
authenticated `POST /api/adapter/recipes/import-candidate/dry-run` route in
that external workspace. The opt-in image is
`local/vanilla-cookbook-adapter:0033y`; it is not the default image and has no
commit behavior. 0033Z adds a separately gated authenticated commit adapter in
the `0033z` image; it remains local-only and requires explicit confirmation.
0034A now proves service-level core ownership and a real temporary SQLite commit
with backup/restore using a synthetic `AuthUser`. Route-level session handling
remains intentionally unverified, so sidecar UI real-save wiring is still not
ready. 0034C now provides a core-process dev-only fixture that verifies the
full sequence without exporting credentials; it does not change that sidecar
UI status.

Identity and storage are a separate future core boundary. The [Google-first
OIDC and Future Storage Authorization ADR](google-first-oidc-storage-auth-architecture.md)
selects Google as the first planned sign-in provider, keeps Drive consent
separate from login, and identifies Microsoft/OneDrive as the next provider to
evaluate. The sidecar does not own core sessions, cookies, provider tokens, or
storage grants; production Save-to-Cookbook remains unimplemented.

## Boundary before platform work

This is a local operator experience and safe link handoff only. It is not a reverse proxy for a
public origin and does not add AWS resources, deployment configuration,
authentication, payment, provider routing, persistent memory, or storage.
Before AWS planning resumes, the local product shell, mock startup guidance,
and offline smoke coverage must remain the validated baseline.
