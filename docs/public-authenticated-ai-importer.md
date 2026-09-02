# Public Authenticated AI Recipe Importer

0034O connects one sidecar workflow to the public Cookbook without publishing
the sidecar itself.

```text
Browser
  -> Cloudflare Tunnel
  -> Vanilla Cookbook core (Google/Lucia session required)
  -> allowlisted server-side importer proxy
  -> private ai-api container
  -> OpenAI Responses API / gpt-5.4-nano
```

The public edge still targets `app:3000`. No new hostname, DNS record, tunnel
route, or Cloudflare dashboard change is needed. Core and sidecar share the
existing `cookbook-public-tunnel` Docker network; only core has the `app`
alias. The sidecar exposes port 8000 only inside that network.

## Public feature

Authenticated users see **AI recipe assistant** in desktop and mobile
navigation. `/ai` accepts pasted recipe text plus an optional source note and
shows a structured draft for review. This first slice does not save the draft.

Core exposes only `POST /api/ai/import-recipe`. It checks the real core session,
limits input to 12,000 characters, permits three requests per user per five
minutes, pins `openai/gpt-5.4-nano`, and forwards no cookie, identity, OAuth
artifact, or browser authorization header.

## Internal authentication and budgets

Copy `public-ai.env.example` to ignored `.env.public-ai`, then generate a
distinct random value for both `AI_SIDECAR_OPERATOR_TOKEN` and
`AI_OPERATOR_GATE_TOKEN`. The same ignored file is supplied to core and
sidecar. Core injects the first name server-side; the sidecar hashes the second
for comparison through its existing operator gate. The browser never sees it.

The public Compose profile enables only the `importer` workflow and disables
the local bypass. Live provider calls remain bounded to ten calls per sidecar
runtime budget context, 1,000 output tokens per call, 13,000 total estimated
tokens per call, 0.05 USD estimated cost per call, and 0.25 USD per runtime
budget context. The separate manual live-test ceiling remains 25 cents.

## Runtime

Set the two environment variables to the ignored core files before using the
public Compose profile:

```powershell
$env:PUBLIC_CORE_ENV_FILE = 'C:\Users\scott\projects\vanilla-cookbook-core\.env'
$env:PUBLIC_CORE_OIDC_ENV_FILE = 'C:\Users\scott\projects\vanilla-cookbook-core\.env.public'
docker compose -f docker-compose.public.yml up -d --build
```

This profile intentionally does not recreate the existing remotely managed
Cloudflare connector. The known-working connector remains independently
attached to `cookbook-public-tunnel` and continues to resolve the `app` alias.
This prevents a stale sidecar-repository tunnel placeholder from replacing the
working connector token.

The existing Docker-managed `cookbook-public-core-db` and
`cookbook-public-core-uploads` volumes are external and retained across
replacement.

## Excluded routes and data

The proxy does not expose the sidecar demo, config, admin, invite,
recipe-session, dataset, search, Ask My Cookbook, meal-plan, or local-save
routes. The sidecar receives no Cookbook database/upload mount, so this slice
cannot read another user's saved recipes or write canonical data.

Rollback is to disable `AI_SIDECAR_ENABLED` or restore the prior core image;
the existing public homepage, login, recipe storage, and tunnel route remain
independent.
