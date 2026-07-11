## 0029H Public Route Exposure Review Results

### Summary

Completed the public route exposure review for the AI sidecar. The work is documentation- and test-focused only; no public route exposure, Cloudflare change, auth layer, or storage change was added.

### What changed

- Added [AI Public Route Exposure Review](../docs/ai-public-route-exposure-review.md) with a route inventory, exposure categories, proxy boundary guidance, CORS guidance, a go/no-go checklist, and abuse/rate-limit placeholders.
- Added `ai-api/tests/test_ai_route_exposure_review.py` to verify the hidden admin usage report, route categorization, secret-free OpenAPI/schema content, operator-gated report access, invite-session defaults, and budget-gated live provider decisions.
- Updated the live demo runbook, operator gate doc, budget doc, invite-session doc, usage-report doc, recipe-session acceptance runbook, eval plan, feature status, implementation backlog, and README with the exposure review boundary.

### Route inventory summary

- `GET /health` is the main public candidate.
- `GET /demo` and `GET /demo/ai` are public candidates only if the demo UI is intentionally published later.
- `GET /demo/readiness` and `GET /ai/config` are internal status routes.
- `GET` and `POST /recipes/search` and `/dataset/search` are local-only deterministic search routes.
- `POST /dataset/ask`, `POST /ai/import-recipe`, `POST /ai/ask`, `POST /ai/meal-plan`, and `/ai/recipe-session/*` are invite-only candidates only after further gating, budget, proxy, and CORS controls.
- `/ai/invite/*` control routes are operator-only or internal status.
- `GET /ai/admin/usage-report` is never-public.

### OpenAPI exposure findings

- The admin usage-report route remains hidden from OpenAPI.
- Demo and readiness routes stay hidden from OpenAPI.
- The OpenAPI schema remains free of the forbidden token, credential, prompt, response, and local-path markers checked by the tests.

### Cloudflare and reverse-proxy recommendations

- Public edge routing should stay path-specific, not `/ai/*` broad.
- `/ai/admin/*` should stay blocked at the edge.
- `/ai/invite/*` and `/ai/recipe-session/*` should stay private until a later explicit exposure review.
- `/dataset/*` and `/recipes/search` should remain private unless the exposed data boundary is intentionally public-safe.

### CORS recommendations

- Use explicit allowlists only.
- Do not use wildcard origins for public AI routes.
- Keep `X-AI-Operator-Token` and `X-AI-Demo-Session-Token` private browser headers, not broadly allowed public headers.
- Verify preflight behavior before any public launch.

### Go/no-go checklist

- Operator gate reviewed.
- Invite session flow tested.
- Provider budget enforcement tested.
- Usage report reviewed.
- Route inventory updated.
- Admin/operator endpoints hidden and blocked at the proxy layer.
- CORS restricted.
- Live opt-in confirmed.
- Secret scan passed.
- Evals passed.
- Mock smoke passed.
- Abuse and rate-limit strategy documented.
- Logging reviewed.
- Rollback plan documented.

### Validation results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed, 39/39 offline cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api/tests/test_ai_route_exposure_review.py -q` passed, 7/7.
- `& .\.venv\Scripts\python.exe -m pytest ai-api/tests/test_ai_usage_report.py ai-api/tests/test_demo_ui.py -q -k 'not seeded_demo_data_supports_saved_recipe_workflows'` passed, 11/11 selected and 1 deselected.
- `& 'C:\Program Files\Git\bin\bash.exe' scripts/validate-repo.sh` passed, including shell syntax, Docker Compose config, full AI test suite, eval harness, Markdown link checks, and secret-pattern scan.
- `docker compose config --quiet` passed.
- `git diff --check` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1` skipped cleanly because live opt-in was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1` skipped cleanly because live opt-in was not set.

### Explicit non-goals

- No public route exposure.
- No Cloudflare changes.
- No DNS changes.
- No auth, login, OAuth/OIDC, paid access, or payment integration.
- No production storage, Redis, Postgres, or SQLite persistence.
- No live OpenAI calls during normal validation.
- No generated artifacts, logs, screenshots, credentials, or tokens committed.

### Artifact safety confirmation

- No raw invite/session tokens.
- No raw provider prompts or responses.
- No `.env` values.
- No local absolute paths in public docs examples.
- No production session storage.
- No payment secrets.
- No Cloudflare config changes.

