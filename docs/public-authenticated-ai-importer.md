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

## Transient provider recovery

0034P distinguishes retryable provider failures from deterministic failures.
Timeouts, network errors, temporary provider failures, and incomplete
structured output permit exactly one core-owned retry. The second call passes
through the same sidecar operator gate and provider budget check, so it counts
against the configured call and cost caps. Account/quota, authentication,
model, schema, payload, rate-limit, and authorization failures are never
retried. If the retry also fails, the UI reports that one bounded retry was
used without exposing provider internals.

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

The ignored host `recipe-dataset/` directory is mounted read-only at
`/app/recipe-dataset` in the sidecar only. `RECIPE_DATASET_INDEX_LIMIT=5000`
retains the documented meaningful-RAG profile while keeping retrieval bounded.
Compose uses `create_host_path: false` so a missing dataset fails deployment
instead of silently creating an empty directory and degrading to no-RAG
drafting. No dataset file is copied into an image, committed, mounted into
core, or exposed through the public edge.

The public sidecar warms this bounded in-memory index before reporting healthy.
Its health-check startup allowance is 120 seconds, keeping the approximately
one-minute first index build out of the first user's request path. Normal tests
and non-public runtimes leave warmup disabled by default.

## Visible grounding provenance

0034R adds a provenance panel below a successful AI draft. The authenticated
core proxy returns only whether the draft met the strong grounding policy,
bounded retrieved/used/citation counts, allowlisted relevance and support
labels, and at most three deduplicated citation titles. The browser does not
receive retrieval queries, record or source IDs, snippets, scores, paths,
packed context, support reasons, prompts, provider responses, or index details.

When the configured dataset is available, the panel lets a user distinguish a
strongly grounded draft from one where local examples were merely reviewed.
Warnings remain visible separately and continue to describe degraded dataset
availability without exposing local filesystem details.

0034S removes a redundant dataset scan from the warmed request path. The
context packer now reads ingredients and instruction summaries from the same
fingerprinted in-memory index already used for deterministic retrieval. The
index owns a source-ID lookup built during startup, so repeated requests do not
reparse and remap all 5,000 records. Existing cache TTL, file-fingerprint
invalidation, record bounds, rankings, citations, and support policy remain in
effect; no persistent index artifact is created.

0034T removes two more sources of repeated scoring work without pruning the
candidate set or changing the scoring formula. Query anchors are normalized
once per search rather than once per document, and each indexed field keeps
exact token set/sort structures for equivalent bidirectional prefix matching.
All 5,000 bounded documents are still scored deterministically. A real-dataset
warm novel query fell from approximately 9.4 seconds to approximately 0.28
seconds; repeated retrieval-cache hits remain faster still.

## Excluded routes and data

The proxy does not expose the sidecar demo, config, admin, invite,
recipe-session, dataset, search, Ask My Cookbook, meal-plan, or local-save
routes. The sidecar receives no Cookbook database/upload mount, so this slice
cannot read another user's saved recipes or write canonical data.

Rollback is to disable `AI_SIDECAR_ENABLED` or restore the prior core image;
the existing public homepage, login, recipe storage, and tunnel route remain
independent.
