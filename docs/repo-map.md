# Repository Map

| Path | Purpose |
| --- | --- |
| `.github/workflows/` | Manual EC2 control/deployment through OIDC and SSM. |
| `.gitattributes` | Repository text normalization rules, including LF checkout for shell scripts. |
| `ai-api/` | Minimal FastAPI AI sidecar with health/config endpoints, read-only recipe reader modules, deterministic recipe search, mock/OpenAI provider harness, and offline tests. |
| `docs/` | Architecture, deploy, configuration, backup, restore, and operations guides. |
| `inbox/` | Numbered task specifications; never store secrets here. |
| `outbox/` | Matching implementation and validation reports. |
| `scripts/` | Bootstrap, preflight, repository validation, verification, backup, restore, and listing helpers. |
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
- [AI sidecar architecture](ai-sidecar-architecture.md)
- [AI schema notes](ai-schema-notes.md)
- [AI evals plan](ai-evals-plan.md)
- [AI implementation backlog](ai-implementation-backlog.md)
