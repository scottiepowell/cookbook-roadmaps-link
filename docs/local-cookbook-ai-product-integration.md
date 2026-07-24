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

## Boundary before platform work

This is a local operator experience and safe link handoff only. It is not a reverse proxy for a
public origin and does not add AWS resources, deployment configuration,
authentication, payment, provider routing, persistent memory, or storage.
Before AWS planning resumes, the local product shell, mock startup guidance,
and offline smoke coverage must remain the validated baseline.
