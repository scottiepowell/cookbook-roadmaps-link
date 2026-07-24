# 0033Q Local Save-to-Cookbook Readiness Evidence Harness Results

Status: complete, local-only and disposable.

## Result

Added `scripts/test-save-to-cookbook-local-readiness.ps1` and the deterministic
helper `ai-api/app/local_save_readiness.py`. The harness requires
`-ApproveLocalWrite`, the `cookbook-local` Compose project, and a loopback HTTP
target. It rejects exposed/production, AWS, GitHub, Cloudflare, tunnel, and
non-loopback inputs before any backup or write.

## Evidence run

With Docker Desktop running, the harness verified the app-only local Compose
project and localhost readiness, then created a temporary backup of the
ignored disposable DB/uploads. It used one synthetic local owner and one
synthetic recipe with no categories, media, uploads, or embeddings.

The run proved:

- deterministic ingredient lines and numbered direction text round-tripped;
- servings were serialized as invariant text;
- synthetic ownership and local read-after-write succeeded;
- duplicate prevention and same-key replay/conflict decisions were reported;
- an invalid-owner transaction failure rolled back;
- DB/uploads were restored and the local app restarted before success.

The idempotency result is harness-level because the discovered upstream schema
has no idempotency column. It proves that the harness does not perform a
second successful write; it is not a claim that the native app has persistent
idempotency semantics.

## Validation

- Focused adapter/readiness tests: 21 passed.
- The approved local readiness harness: passed with restore.
- No live OpenAI call or provider key was used.
- No production or exposed deployment was inspected or targeted.

Full repository validation is recorded with the final task run. Runtime DB,
uploads, temporary backup data, and all fixture contents remain uncommitted.

## Remaining boundary and non-goals

This evidence does not implement a Save-to-Cookbook button, public route,
commit endpoint, native authenticated core-app adapter, production write-back,
migration, or UI/API integration. It does not prove native API/UI behavior or
production compatibility. It adds no auth, SSO/BYOS, analytics, ads, payment,
AWS, GitHub Actions, Cloudflare, provider routing, QMD, or live-call work.
The next implementation task must separately review native adapter ownership,
API transaction behavior, and any production approval before mutation.
