# AI UI Integration Plan

## Current Approach

The first AI UI integration is served by the FastAPI AI sidecar at:

```text
GET /demo
GET /demo/ai
```

This is intentional. The repository runs Vanilla Cookbook from an external Docker image and does not contain the upstream Vanilla Cookbook frontend source tree. A sidecar-served demo page lets the completed AI workflows be exercised from a browser without rewriting or vendoring the upstream application UI.

The production-quality live demo flow is documented in [AI Live Demo Runbook](ai-live-demo-runbook.md).

## How To Open Locally

Start the AI sidecar with the normal local development approach, then open:

```text
http://127.0.0.1:8000/demo
```

The page uses static files served from `ai-api/app/static/`:

- `demo.html`
- `demo.css`
- `demo.js`

The UI includes a readiness panel backed by:

```text
GET /demo/readiness
```

Readiness reports safe status only: sidecar health, provider mode/model, offline demo mode, saved-recipe availability/count, and local dataset availability. It does not expose local filesystem paths or sensitive runtime values.

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

## Missing Local Data

Saved-recipe workflows need a configured cookbook SQLite database. Dataset workflows need a configured local dataset directory. If either is missing, the API returns controlled errors or warnings and the UI shows a friendly message instead of exposing local private paths.

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
