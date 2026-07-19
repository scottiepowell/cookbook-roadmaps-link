# Local Cookbook AI Product Integration

## Decision

The local integration uses a sidecar-served product shell. Open
`http://127.0.0.1:8000/product` first; it presents Vanilla Cookbook and the AI
workflows as one local product while preserving their ownership boundary.

| Route | Role |
| --- | --- |
| `/product` | Local entry point, safe readiness, and operator guidance. |
| `/product/cookbook` | Redirect to the local external Vanilla Cookbook container on port 3000. |
| `/product/ai` | Redirect to the existing sidecar AI workspace at `/demo`. |
| `/demo` | Existing AI Recipe Creator, Recipe Session, Ask, Dataset, and Meal Plan UI. |

Vanilla Cookbook runs from the `jt196/vanilla-cookbook:stable` external image
and its editable frontend source is not in this repository. The shell is
therefore intentionally a link integration rather than an upstream UI rewrite
or vendored copy.

## Local operation

`scripts\start-ai-demo-local.ps1` generates a temporary local SQLite/database
fixture and small dataset fixture, starts the sidecar on port 8000, and prints
the product URL. Start Docker Compose separately when the upstream Cookbook
container is needed on port 3000. If product readiness reports missing saved
recipes or dataset data, restart the seed/start script; generated artifacts
remain ignored.

The launcher automatically imports ignored local `.env` values only when the
corresponding process variable is absent. A valid local live profile uses
`AI_PROVIDER=openai`, `OPENAI_ENABLE_LIVE_TESTS=true`,
`OPENAI_MODEL=gpt-5.4-nano`, a 1–300 output-token cap, a 1–25 cent budget, and
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

## Boundary before platform work

This is a local operator experience only. It is not a reverse proxy for a
public origin and does not add AWS resources, deployment configuration,
authentication, payment, provider routing, persistent memory, or storage.
Before AWS planning resumes, the local product shell, mock startup guidance,
and offline smoke coverage must remain the validated baseline.
