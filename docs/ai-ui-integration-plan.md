# AI UI Integration Plan

## Current Approach

## Local Product Shell

The local integration pattern is a sidecar-served product shell, not a rewrite
of Vanilla Cookbook. `GET /product` is the first local operator URL. It links
to the configured external Vanilla Cookbook target at `GET /product/cookbook` and to
the existing sidecar workspace at `GET /product/ai` (which redirects to
`/demo`). This keeps the upstream image at `127.0.0.1:3000` and the AI sidecar
at `127.0.0.1:8000` while presenting one local product entry point. The
non-secret `COOKBOOK_TARGET_URL` setting can select an exposed Cookbook URL;
unset or invalid values fall back to the local Compose target.

The repository does not contain editable upstream Vanilla Cookbook frontend
source, so direct navigation or panel integration in that app is deliberately
out of scope. The shell reads only the existing safe readiness endpoint and
does not proxy production traffic, expose secrets, or change public routing.
When the local Cookbook container is unavailable, the product page tells the
operator to start Compose and refresh; `/product/ai` remains an independent
sidecar handoff to `/demo`.

The first AI UI integration is served by the FastAPI AI sidecar at:

```text
GET /demo
GET /demo/ai
```

This is intentional. The repository runs Vanilla Cookbook from an external Docker image and does not contain the upstream Vanilla Cookbook frontend source tree. A sidecar-served demo page lets the completed AI workflows be exercised from a browser without rewriting or vendoring the upstream application UI.

The production-quality live demo flow is documented in [AI Live Demo Runbook](ai-live-demo-runbook.md).

## How To Open Locally

Start the AI sidecar with the normal local development approach, then open:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Then open:

```text
http://127.0.0.1:8000/demo
```

The start script seeds generated local demo data and starts the sidecar on `127.0.0.1:8000`. It sets `AI_PROVIDER=mock`, `COOKBOOK_DB_PATH`, and `RECIPE_DATASET_DIR` for the current process only. It does not write to production cookbook data.

The page uses static files served from `ai-api/app/static/`:

- `demo.html`
- `demo.css`
- `demo.js`

The UI includes a readiness panel backed by:

```text
GET /demo/readiness
```

Readiness reports safe status only: sidecar health, provider mode/model, offline demo mode, saved-recipe availability/count, and local dataset availability. It does not expose local filesystem paths or sensitive runtime values.

## Local browser troubleshooting

`tests/ui/cookbook-ai-mode.spec.ts` is an optional Playwright Chromium harness
for local `/product` and `/demo` QA. It verifies selector propagation,
normalized request preferences, safe mock/live-unavailable states, and desktop
layout bounds without requiring live OpenAI. See
[Playwright UI Troubleshooting](playwright-ui-troubleshooting.md).

The Playwright runner intentionally requires a `mock/mock-basic` sidecar. It
is evidence for selector propagation and safe unavailable behavior, not a
live-provider acceptance tool.

## Workflows Exercised

The demo UI calls existing endpoints only:

| UI Section | Endpoint |
| --- | --- |
| Health | `GET /health` |
| Provider status | `GET /ai/config` |
| Structured recipe importer | `POST /ai/import-recipe` |
| Ask My Cookbook | `POST /ai/ask` |
| Dataset search | `GET /dataset/search` |
| Dataset Ask/RAG | `POST /dataset/ask` |
| Meal planner | `POST /ai/meal-plan` |

The UI displays readable answer summaries, JSON previews behind expandable details, citations/provenance, warnings, provider/model metadata, retrieval counts, loading states, reset controls, and friendly errors.

## Local Demo Data

Saved-recipe workflows need a configured cookbook SQLite database. Dataset workflows need a configured local dataset directory. For local mock demos, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\seed-ai-demo-data.ps1
```

This writes a small generated fixture under `.tmp-ai-demo/` by default. If either data source is missing, the API returns controlled errors or warnings and the UI shows a friendly message instead of exposing local private paths.

## Screenshot And Demo Support

This UI is a safer source for future screenshots because it uses the sidecar API directly and avoids showing environment files, provider keys, raw local dataset files, or private system configuration. Future screenshot work should still follow [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md).

## Deferred Work

This task does not add:

- upstream Vanilla Cookbook frontend changes;
- production storage architecture;
- deployment or Cloudflare changes;
- controller/demo launch workflows;
- embeddings or vector database infrastructure;
- browser automation;
- committed screenshots.
