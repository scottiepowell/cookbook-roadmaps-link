## 0030J 29/30 Integrated Regression And E2E Harness Results

### Summary

Completed the integrated 29/30 regression harness for the local AI demo baseline. The new runner exercises the combined 0029 guardrail track and the 0030 Recipe Session Alpha track in mock/offline mode by default, with an explicit live-smoke boundary that stays opt-in.

### What changed

- Added [`scripts/e2e-ai-29-30-regression.py`](../scripts/e2e-ai-29-30-regression.py).
- Added [`scripts/run-ai-29-30-regression.ps1`](../scripts/run-ai-29-30-regression.ps1).
- Added [`ai-api/tests/test_ai_29_30_regression_harness.py`](../ai-api/tests/test_ai_29_30_regression_harness.py).
- Added [`docs/ai-29-30-regression-e2e-harness.md`](../docs/ai-29-30-regression-e2e-harness.md).
- Updated the backlog, feature status, live runbook, recipe-session acceptance runbook, route-exposure review, provider budget doc, invite-session flow doc, admin usage-report prototype, monetization ADR, eval plan, and README so the locked baseline and the `0031A` follow-on are visible.

### Integrated flow implemented

- health/config/readiness checks;
- operator gate disabled-by-default and enabled-test-context checks;
- invite sessions disabled-by-default and enabled-test-context checks;
- invite grant creation and redemption;
- protected importer, recipe-session, dataset ask, saved-recipe ask, and meal plan calls with invite-session access;
- provider budget allow/skip behavior in mock/offline mode;
- blocked provider-budget behavior that stops before provider invocation;
- usage-report retrieval and safe count verification;
- OpenAPI hiding for the admin usage report;
- route exposure and monetization boundary assumptions.

### 0029 Controls Covered

- `0029C` safe model serialization and budget snapshot assumptions;
- `0029D` operator gate allow/block behavior;
- `0029E` budget guard allow/skip/block behavior;
- `0029F` invite grant/session create/redeem/block behavior;
- `0029G` usage-report summaries and thresholds;
- `0029H` public-route exposure assumptions and OpenAPI hiding;
- `0029I` monetization and entitlement boundary separation.

### 0030 Controls Covered

- detailed requests create drafts;
- vague requests ask clarification instead of faking a draft;
- material follow-ups trigger refreshes;
- chatter/format-only follow-ups avoid wasteful refreshes;
- finalize stays demo-only and local-safe;
- missing or expired sessions block safely;
- response serialization stays free of raw prompts, raw provider responses, secrets, and local paths.

### Optional Live-Smoke Behavior

- live-smoke checks stay disabled unless explicitly opted in;
- the harness exposes an explicit `--live-smoke` boundary for manual use;
- the wrapper keeps offline validation stable by default;
- live mode is still budget-gated and not part of normal validation.

### Validation Results

- `& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py` passed in offline mode.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ai-29-30-regression.ps1` passed in offline mode.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_29_30_regression_harness.py -q` passed.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` remains expected to pass once rerun after the full patch set.
- `git diff --check`, `docker compose config --quiet`, `scripts\demo-ai-mock.ps1`, `scripts\demo-ai-live-smoke.ps1`, and `scripts\run-openai-demo-evals.ps1` remain part of the required validation set.

### Explicit Non-Goals

- no GLM provider integration;
- no secondary-provider routing;
- no production auth;
- no user accounts or login UI;
- no OAuth/OIDC;
- no paid access, checkout, subscriptions, billing portal, invoices, taxes, refunds, or payment integration;
- no ad, sponsor, or affiliate runtime code;
- no public route exposure;
- no Cloudflare or DNS changes;
- no production storage, Redis, Postgres, or SQLite persistence;
- no persistent user memory;
- no browser automation, screenshots, or generated artifacts;
- no live OpenAI calls during normal validation.

### Artifact Safety Confirmation

- no raw invite/session tokens were committed;
- no raw operator tokens were committed;
- no raw provider prompts or responses were committed;
- no payment secrets or ad network IDs were committed;
- no sponsor secrets or contracts were committed;
- no local absolute paths were added to public docs examples;
- no production session storage was added.

### Recommendation For `0031A`

`0031A: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` should compare against this locked baseline and remain disabled by default until a separate ADR and implementation task explicitly approve it.
