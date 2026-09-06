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
navigation. `/ai` accepts a recipe idea plus an optional source note, asks a
clarifying question when needed, and shows a structured draft for review. The
same composer remains available for natural-language changes to that draft.
This flow does not save the draft.

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

The public Compose profile enables only the `importer` and `recipe_session`
workflows and disables the local bypass. Live provider calls remain bounded to
44 calls per sidecar runtime budget context, 1,800 output tokens per call,
13,800 total estimated
tokens per call, 0.05 USD estimated cost per call, and 0.25 USD per runtime
budget context. The separate manual live-test ceiling remains 25 cents.

## Transient provider recovery

0034P distinguishes retryable provider failures from deterministic failures;
0035A raises the recovery ceiling to three core-owned retries. Every attempt
passes through the same sidecar operator gate and provider budget check, so it
counts against the configured call and cost caps. Account/quota,
authentication, model, schema, payload, rate-limit, and authorization failures
are never retried. The UI reports the latest request's safe retry count below
the change count without exposing provider internals.

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

## Bounded recipe conversation

0034U exposes only the recipe-session start and message operations through two
authenticated core routes. Core creates an opaque public chat UUID, binds it to
the current core user, and keeps the sidecar interaction ID server-side. Both
maps expire after one hour and are intentionally in-memory, so deployment or
process restart ends active chats.

The initial request can return a deterministic clarification question without
consuming one of the ten post-draft changes. Each revision sends the current
bounded draft and latest requested change through the same importer, nano-model,
RAG, operator-gate, and budget path. At ten changes, both the sidecar and public
response refuse further revisions. Social chatter and replacement confirmation
do not consume a change.

A follow-up that explicitly asks to start over or appears to name a different
dish returns a confirmation state without mutating the draft. The browser can
keep the current recipe or explicitly start a new chat from the proposed idea.
Recipe, ingredient, instruction, and grounding panels use native collapsible
controls with plus/minus indicators to keep long drafts manageable.

0035B makes that replacement decision context-aware. A staple swap is treated
as a likely dish switch only when its named source is absent from the current
draft; the same request remains a normal revision when that source is present.
Wording that asks to make the draft more like another dish also pauses for
confirmation, as do explicit switch, go-with, change-this, instead-do,
scrap-and-make, and new-recipe phrases.

0035C keeps the prompt usable for typed yes/no answers or a clearer replacement
idea. Confirmation removes the old core-owned chat binding and starts a new
sidecar session using only the extracted proposal; `start a new recipe with
...` performs the same clean restart directly. Until confirmation, the draft
and successful-change count do not change.

0035D adds a deterministic coherence check before revision commit. Pasta-bake
and fried-rice candidates must retain their expected base and method anchors,
major proteins must be used in their instructions, and explicit stale omelet
directions cannot survive under another dish title. A rejected candidate uses
the safe retryable transactional path and never replaces the current draft.

0034V makes follow-up mutation transactional. The sidecar stages requirements
and invokes the provider before committing any new requirements, draft, or
revision count. A failed attempt therefore cannot consume a change or partially
alter future context. Retryable timeout, network, temporary-provider, invalid
JSON, and incomplete-output failures expose only a bounded classification to
core and receive up to three identical retries under 0035A. Authorization, quota, configuration,
model, schema, payload, and budget failures are not retried.

The UI treats its outgoing user bubble as optimistic. If the bounded request
still fails, it removes that bubble and restores the request text in the
composer. The current recipe remains visible and the successful-change counter
does not advance. The 1,800-token output ceiling accommodates full structured
recipe revisions; 44 allowed provider attempts cover four attempts for an
initial generation and each of ten changes, while the existing cost ceilings
remain the final budget guard.

0034Z removes provider discretion from serving-only ingredient math. The latest
explicit numeric or written serving target replaces older session-history
targets; double and halve requests resolve from the displayed current yield.
Every parseable numeric ingredient quantity is scaled from the current draft by
the same ratio while ingredient identity and units remain fixed. The model may
adjust pans, batches, and other non-linear instructions, but it cannot change
the committed serving count or ingredient scaling. Mixed serving/content edits
must still return the exact requested yield before commit.

0034Y adds revision identity enforcement before that transactional commit. The
provider receives a locked-invariant instruction to preserve the existing dish,
base starch, protein, method, ingredients, and instruction actions except where
the follow-up explicitly changes them. A deterministic check then rejects a
candidate whose instructions lose an established identity anchor or whose
draft introduces an unrequested conflicting anchor. The sidecar reports only a
safe retryable drift category; it never returns the rejected candidate. An
explicit replacement such as pasta with rice is still allowed.

0034W preserves initial prompt fidelity. The recipe-session start route passes
the complete user request to importer retrieval and generation rather than
reconstructing it from a necessarily limited deterministic parser. The parser
still supplies clarification, replacement, retrieval, and diff signals, but it
no longer acts as a lossy filter before generation. Cauliflower, generic cheese,
and mushrooms are tracked explicitly; modifiers such as `riced` remain present
in the full generation text.

0034X gives initial generation the same bounded transient recovery policy as
recipe changes. Core creates one opaque request ID, uses it as the sidecar
idempotency key and safe trace ID, and sends the identical body on retries.
0035A permits up to three retries within a 90-second total deadline. Sidecar serializes the
same key, returns a completed session on replay, resumes the same uncommitted
session after a failed first attempt, and rejects a key reused with different
request content. This prevents retry-created duplicate sessions.

The sidecar also reuses one OpenAI HTTP client per safe key fingerprint and
timeout configuration so repeated calls can reuse pooled connections. Safe
structured logs now distinguish retrieval, provider, validation, total
sidecar, and core-proxy duration. They contain no recipe text, prompt, response,
credential, cookie, OAuth value, or user profile. The provider-attempt ceiling
is 44: four initial attempts and up to four attempts for each of ten changes.
Redis, asynchronous jobs, and Protocol Buffers remain outside this task.

Compound prompts such as adding potatoes while doubling servings remain edits
to the current recipe. The sidecar uses the existing draft as dish context,
requires the requested addition, sets the exact yield, and deterministically
scales every established numeric ingredient before committing the revision.

## Excluded routes and data

The core does not expose the sidecar demo, config, admin, invite, arbitrary
recipe-session IDs, dataset, search, Ask My Cookbook, meal-plan, or local-save
routes. The sidecar receives no Cookbook database/upload mount, so this slice
cannot read another user's saved recipes or write canonical data.

Rollback is to disable `AI_SIDECAR_ENABLED` or restore the prior core image;
the existing public homepage, login, recipe storage, and tunnel route remain
independent.
