# 0030I-8R live diagnostic environment and port preflight correction

The prior operator output was contradictory: the diagnostic printed a desired
`gpt-5.4-nano` request while a stale inherited model value caused
`model_not_allowed`; startup also attempted Uvicorn while port 8000 was already
occupied. The root cause was `OnlyIfMissing` environment loading combined with
a hardcoded diagnostic display.

The diagnostic now trims and validates `OPENAI_MODEL` and optional `AI_MODEL`
independently, reports safe `allowed`/`not_allowed`/`missing` statuses, and
identifies which field contains a stale value. `-PreflightOnly` is an explicit
no-call mode; the existing no-approval path remains no-call. A valid preflight
still requires explicit `-ApproveLiveCall` before one bounded importer call.

The local launcher now checks `127.0.0.1:<port>` before generating/launching
Uvicorn. If occupied, it exits with safe `netstat` and operator-recognized
sidecar guidance and never auto-kills a process.

Deterministic tests cover stale model fields, whitespace normalization, valid
no-call preflight, approval gating, occupied-port refusal, and safe output
boundaries. No live provider call was made for this correction.

Validation: env-file loader passed; offline evals passed; Git Bash validator
passed; `git diff --check` and Docker Compose config passed; mock smoke passed;
live wrappers skipped; Playwright remains mock-only. Direct Windows pytest may
still encounter the known `pytest-of-scott` temp ACL issue.

Explicit non-goals: no live success claim, retries, secrets, provider bodies,
AWS/platform work, production storage/auth, public exposure, screenshots,
browser artifacts, vector DB, embeddings, raw datasets, persistent indexes, or
disk cache.

Follow-up one-call live diagnostic is ready only after the no-call preflight
reports valid model/configuration and the operator confirms the correct sidecar
owns the port; it was not run here.
