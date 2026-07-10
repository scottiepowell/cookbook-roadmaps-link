# 0029F Invite-Only Demo Session Flow Results

## Summary

Implemented a local/private invite-only demo session layer on top of the existing AI demo access and metering scaffold. The feature is disabled by default, process-local, and intended for controlled operator use and offline/mock validation.

## What Changed

- Added `ai-api/app/ai_invite_sessions.py` with a bounded process-local invite grant/session store.
- Added invite endpoints for grant creation, redemption, status, retrieval, revocation, and a safe status view.
- Wired invite sessions into protected demo workflows so a valid invite session token can authorize allowed workflows when the feature is enabled.
- Added safe invite-session response handling so raw tokens are only exposed at creation time if the local operator flow chooses to return them.
- Added mock smoke support for an optional invite-session path.

## Token And Fingerprint Safety

- Invite tokens and session tokens are fingerprinted before storage.
- Safe status and retrieval views do not expose raw tokens.
- Protected workflows use `X-AI-Demo-Session-Token` only when invite sessions are explicitly enabled.
- No secrets, `.env` values, raw prompts, raw provider responses, or local paths are returned.

## Operator Gate And Budget Integration

- Local operator gate protection is reused for invite grant creation and revocation when the gate is enabled.
- Provider budget enforcement uses the invite session/grant context so invite sessions can carry workflow and cost limits.
- Invite demo access remains separate from production auth or public access.

## Tests Added

- invite feature disabled behavior;
- grant creation and single-use redemption;
- safe status responses;
- wrong-token, expired, revoked, and disallowed-workflow blocking;
- protected importer access through a valid invite session token;
- forbidden-string leakage checks;
- demo UI coverage for the invite-session hints.

## Documentation Updated

- `README.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`

## Validation

Validation completed successfully:

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
- `git diff --check`
- `docker compose config --quiet`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`

The mock smoke script exercised the default offline path and kept invite sessions disabled unless the optional `AI_INVITE_SMOKE_ENABLED=true` path is explicitly turned on. The live smoke and live eval wrappers skipped cleanly without opt-in.

## Explicit Non-Goals

- no production auth;
- no user accounts;
- no login UI;
- no OAuth/OIDC;
- no paid access;
- no payment integration;
- no invite emails;
- no public route exposure;
- no production storage;
- no Redis, Postgres, or SQLite persistence;
- no persistent user memory;
- no admin dashboard UI;
- no live OpenAI calls during normal validation.

## Artifact Safety Confirmation

No raw invite tokens, session tokens, secrets, provider prompts, provider responses, dataset files, `.tmp-ai-demo` artifacts, or local absolute paths were committed.
