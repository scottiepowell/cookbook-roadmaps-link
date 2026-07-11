## 0029I Monetization And Entitlement Boundary ADR Results

### Summary

Completed the monetization and entitlement boundary ADR as a docs-only decision record. The repo now states that near-term monetization should come from ads, sponsorships, partner placements, and clearly disclosed affiliate links, while paid access remains out of scope for now.

### What changed

- Added [AI Monetization And Entitlement Boundary ADR](../docs/ai-monetization-and-entitlement-boundary-adr.md).
- Added `ai-api/tests/test_ai_monetization_boundary_docs.py` to verify the ADR text, title references, secret-free content, and the separation between monetization and access/budget/route controls.
- Updated the backlog, feature status, public route exposure review, session metering schema, provider budget enforcement doc, invite-session flow doc, usage-report prototype doc, live demo runbook, eval plan, README, and two related roadmap docs so the new title is used consistently.

### Business decision captured

- Near-term revenue is ads, sponsorships, partner placements, sponsored recipe collections, and clearly disclosed affiliate links.
- User-paid access is not implemented now.
- Future paid advanced features remain only future possibilities and require a separate ADR plus a separate implementation task.

### Technical seams documented

- Access control stays separate from monetization.
- Budget guard stays separate from monetization.
- Invite sessions stay separate from monetization.
- Usage reports stay separate from monetization.
- Route exposure stays separate from monetization.
- Future entitlement concepts are documented as seams only and are not active runtime behavior.

### Policy/disclosure notes captured

- Sponsor and affiliate relationships should be clearly disclosed.
- Native ads and sponsored content should be distinguishable from ordinary recipe content.
- Ad placements should not mislead users.
- Sponsor/ad experiments should have label and unsafe-copy tests.
- Ad network IDs, sponsor contracts, affiliate secrets, and payment keys must not be committed.
- Production monetization still requires separate legal and policy review.

### Validation results

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_monetization_boundary_docs.py -q` passed.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed, 39/39 offline cases.
- `& 'C:\Program Files\Git\bin\bash.exe' scripts/validate-repo.sh` passed, including 282 AI tests and the repo validation checks.
- `git diff --check` passed.
- `docker compose config --quiet` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1` skipped cleanly.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1` skipped cleanly.

### Explicit non-goals

- No payment provider integration.
- No checkout, subscriptions, billing portal, invoices, taxes, or refunds.
- No paid user accounts or premium enforcement.
- No ad network runtime code, sponsor placement runtime code, or affiliate link runtime code.
- No public route exposure, Cloudflare changes, DNS changes, auth changes, or production storage.
- No Redis, Postgres, or SQLite persistence.
- No live OpenAI calls during normal validation.

### Artifact safety confirmation

- No payment secrets.
- No ad network IDs.
- No sponsor secrets or contracts.
- No raw invite/session tokens.
- No raw provider prompts or responses.
- No environment files or other local secret material.
- No logs, screenshots, generated artifacts, or local absolute paths in public docs examples.
