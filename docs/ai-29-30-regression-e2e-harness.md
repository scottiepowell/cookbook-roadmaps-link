# 29/30 Integrated Regression And E2E Harness

## Purpose

This harness locks the combined local AI baseline from `0029` and `0030` before any secondary-provider offload work begins.

It answers a single practical question:

- can a local operator create an invite, redeem it, use protected recipe-session/importer/RAG flows, respect budget controls, observe usage reporting, and preserve route/public/monetization boundaries without leaking secrets or adding live/public behavior by default?

## What It Validates

### 0029 Controls

The harness exercises and checks:

- `0029C` safe session, grant, meter, quality, audit, and budget-snapshot serialization assumptions;
- `0029D` operator gate behavior when enabled and disabled;
- `0029E` provider budget allow/skip/block behavior before invocation;
- `0029F` invite grant/session creation, redemption, inspection, and safe blocking;
- `0029G` usage report counts, warnings, and safe serialization;
- `0029H` route-exposure assumptions and OpenAPI hiding for admin/operator internals;
- `0029I` monetization and entitlement boundary assumptions without runtime payment or ad code.

### 0030 Controls

The harness also checks the Recipe Session Alpha baseline:

- detailed requests create a draft;
- vague requests ask a bounded clarification instead of inventing a draft;
- follow-ups can trigger a material RAG refresh;
- chatter or formatting-only follow-ups do not wastefully refresh;
- finalize is demo-only and local-safe;
- missing or expired sessions block safely;
- response serialization stays free of raw prompts, raw provider responses, secrets, and local paths.

## Default Mode

The default mode is offline/mock only.

The offline run:

- seeds generated local demo data;
- uses process-local invite/session, budget, and usage-report stores;
- runs FastAPI `TestClient` calls instead of browser automation;
- keeps live provider checks disabled.

## Optional Live-Smoke Mode

Live-smoke mode is explicit opt-in.

It is only intended for manual verification after the offline baseline passes, and it should stay behind:

- `AI_29_30_REGRESSION_LIVE=true`;
- `OPENAI_ENABLE_LIVE_TESTS=true`;
- `AI_PROVIDER=openai`;
- a real `OPENAI_API_KEY`;
- the `--live-smoke` flag on `scripts/e2e-ai-29-30-regression.py` or the matching wrapper path.

The live path should remain minimal and budget-gated. It is not part of normal validation.
The wrapper can also read `-EnvFile .\.env`, but the optional live boundary still stays off unless `AI_29_30_REGRESSION_LIVE=true`, `OPENAI_ENABLE_LIVE_TESTS=true`, and `AI_PROVIDER=openai` are set explicitly in the file or process environment.

## Relationship To 0031A

`0031A: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` should use this harness as its comparison baseline.

The GLM work should stay disabled by default until a separate ADR and implementation task explicitly approve it.

## Windows Note

Direct Windows pytest runs can hit the known local `pytest-of-scott` temporary ACL issue for unrelated fixture tests.

If that happens, rely on the Git Bash validation path when it passes and document the Windows ACL failure separately.

## Non-Goals

- no GLM provider integration;
- no secondary-provider routing;
- no production auth;
- no user accounts or login UI;
- no OAuth/OIDC;
- no paid access, billing, checkout, invoices, refunds, or payment integration;
- no ad, sponsor, or affiliate runtime code;
- no public route exposure;
- no Cloudflare or DNS changes;
- no production storage, Redis, Postgres, or SQLite persistence;
- no persistent user memory;
- no browser automation or screenshots;
- no live OpenAI calls during normal validation.
