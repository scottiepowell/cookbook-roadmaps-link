# Repository Map

| Path | Purpose |
| --- | --- |
| `.github/workflows/` | Manual EC2 control/deployment through OIDC and SSM. |
| `.gitattributes` | Repository text normalization rules, including LF checkout for shell scripts. |
| `ai-api/` | FastAPI AI sidecar with health/config endpoints, read-only recipe reader modules, deterministic recipe search, structured recipe import drafts, Ask My Cookbook RAG, saved-recipe meal planner, local dataset inspection/index/search/RAG foundation, mock/OpenAI provider harness, and offline tests. |
| `recipe-dataset/` | Ignored local Kaggle dataset directory for later indexing work; raw files and generated indexes are not committed. |
| `docs/` | Architecture, deploy, configuration, backup, restore, validation, eval, data-boundary, and operations guides. |
| `evals/` | Offline AI cookbook eval harness and generated-fixture cases. |
| `inbox/` | Numbered task specifications; never store secrets here. |
| `outbox/` | Matching implementation and validation reports. |
| `scripts/` | Bootstrap, preflight, repository validation, Windows validation wrapper, verification, backup, restore, local dataset index inspection, AI demo helpers, and listing helpers. |
| `.env.example` | Non-secret template; real host `.env` stays untracked. |
| `docker-compose.yml` | Runs Cookbook and `cloudflared`, persists data, binds app to loopback. |
| `deploy.sh` | Updates `/opt/cookbook`, prepares data, pulls images, reconciles Compose. |

Start with the [README](../README.md), then the [First Deploy Guide](first-deploy-guide.md).

Resume and readiness references:

- [Resume from Windows clone](resume-from-windows-clone.md)
- [Windows local development](windows-local-development.md)
- [Current deployment state](current-deployment-state.md)
- [Codex mailbox continuation](codex-mailbox-continuation.md)

AI design references:

- [AI medium-path roadmap](ai-medium-path-roadmap.md)
- [AI portfolio showcase](ai-portfolio-showcase.md)
- [AI sidecar architecture](ai-sidecar-architecture.md)
- [AI demo walkthrough](ai-demo-walkthrough.md)
- [AI feature status](ai-feature-status.md)
- [AI screenshot capture guide](ai-screenshot-capture-guide.md)
- [AI schema notes](ai-schema-notes.md)
- [Local recipe dataset adapter](local-recipe-dataset-adapter.md)
- [Shared infrastructure data boundaries](shared-infrastructure-data-boundaries.md)
- [Meal planner foundation](meal-planner-foundation.md)
- [AI evals plan](ai-evals-plan.md)
- [AI implementation backlog](ai-implementation-backlog.md)
