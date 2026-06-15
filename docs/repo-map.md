# Repository Map

| Path | Purpose |
| --- | --- |
| `.github/workflows/` | Manual EC2 control/deployment through OIDC and SSM. |
| `docs/` | Architecture, deploy, configuration, backup, restore, and operations guides. |
| `inbox/` | Numbered task specifications; never store secrets here. |
| `outbox/` | Matching implementation and validation reports. |
| `scripts/` | Bootstrap, preflight, repository validation, verification, backup, restore, and listing helpers. |
| `.env.example` | Non-secret template; real host `.env` stays untracked. |
| `docker-compose.yml` | Runs Cookbook and `cloudflared`, persists data, binds app to loopback. |
| `deploy.sh` | Updates `/opt/cookbook`, prepares data, pulls images, reconciles Compose. |

Start with the [README](../README.md), then the [First Deploy Guide](first-deploy-guide.md).
