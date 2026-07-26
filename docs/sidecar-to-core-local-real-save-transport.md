# Sidecar-to-Core Local Real-Save Transport

Status: local/dev-only transport implemented; normal product UI wiring remains deferred.

Date: 2026-07-25

## Boundary

The sidecar now has a small `ai-api/app/cookbook_core_transport.py` client for
the core-owned dev fixture route:

`POST /api/adapter/dev-only/recipes/import-candidate/verify-local-commit`

The client is disabled by default and is not wired into the normal importer UI.
It is an operator/test boundary for a local custom Vanilla Cookbook image, not
a production Save-to-Cookbook feature.

The external core implementation is maintained outside this repository on
branch `openclaw/0034F-sidecar-to-core-local-real-save-transport`, commit
`99641db`. The local image is
`local/vanilla-cookbook-adapter:0034f`; it is opt-in and is not pushed.

## Gates

The transport refuses to send any request unless all of these conditions hold:

- explicit client enablement, approval, and runtime verification;
- Compose project `cookbook-local`;
- exact local image marker `local/vanilla-cookbook-adapter:0034f`;
- HTTP loopback target on port 3000;
- no production, CI, AWS, Cloudflare Tunnel, or tunnel indicators.

The core fixture adds its own independent gates: development mode, explicit
fixture enablement/approval, synthetic fixture mode, the same image marker,
and loopback target. It uses a synthetic in-process core owner and temporary
schema-backed storage. It runs dry-run before commit, verifies a safe UID and
owner read-after-write, checks replay/conflict/duplicate behavior, and rolls
back an invalid-owner failure. Temporary storage is restored and removed.

No cookie, session, token, OAuth value, provider grant, or sidecar-supplied
user identity is accepted or forwarded. No live provider is contacted.

## Payload and response

Only reviewed candidate fields are mapped and sent:

- title, description, integer servings, deterministic ingredient lines;
- deterministic instruction text, safe source/source URL, bounded notes;
- idempotency key plus contract/schema versions;
- explicit local approval.

Tags/categories, media/uploads, remote image fetching, embeddings, prompts,
provider bodies, and raw provider output are excluded. The client filters core
responses to safe status, UID, relative URL, idempotency, duplicate, rollback,
verification, and next-action fields.

The core fixture returns a safe synthetic verification envelope. Its temporary
database means this verification does not make a recipe appear in the normal
persistent Cookbook UI. A future authenticated core-owned transport must be
reviewed separately before UI wiring.

## UI and production status

The existing sidecar UI remains the 0033S review/dry-run/in-memory prototype.
It does not call this transport and does not claim a recipe was saved in
Cookbook. A later task may add a clearly local-only control only after the
operator workflow, core auth boundary, and persistent local target are reviewed.

Production/exposed Save-to-Cookbook and real Google sign-in remain unimplemented.
The sidecar does not own `userId`, sessions, cookies, provider links, tokens,
storage grants, or canonical recipe persistence. Direct sidecar DB writes and
browser/session automation remain rejected.

## Validation

The external focused route and adapter suites passed (35 tests), and the
external Vite build passed. The custom image built locally as `0034f`.
Sidecar unit tests cover disabled/default gates, loopback and deployment
refusal, payload exclusion, safe envelopes, validation, confirmation, and
network failure behavior. Normal validation does not require Docker or a live
provider.

## Explicit non-goals

No production route, normal UI real-save wiring, native persistent save, auth
session transport, migration, direct database write, browser automation,
Google/Microsoft/OpenAI/storage call, deployment work, analytics, ads, payment,
QMD integration, or external source vendoring is included.
