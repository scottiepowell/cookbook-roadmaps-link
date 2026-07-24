# Local Cookbook AI Product Acceptance Checklist

## Prerequisites and start

- Use the repository virtual environment and Docker Compose when the upstream
  Cookbook container is needed.
- For full local integration, start only the Vanilla Cookbook app in Terminal
  1 with `scripts\start-vanilla-cookbook-local.ps1`, then start the AI sidecar
  in Terminal 2 with `scripts\start-ai-demo-local.ps1 -Provider mock`.
- Verify `http://127.0.0.1:3000/` with
  `scripts\check-vanilla-cookbook-local.ps1`; stop it with
  `scripts\stop-vanilla-cookbook-local.ps1`. The local app-only Compose path
  does not require `CLOUDFLARE_TUNNEL_TOKEN`, AWS, GitHub Actions, or a
  production `.env`.
- Start the deterministic mock local product for normal acceptance:

  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
  ```

- Open `http://127.0.0.1:8000/product` first. This is the canonical local
  entry point; `/demo` remains the direct AI workspace.
- With valid ignored `.env`, the same start command launches local live mode
  using only `gpt-5.4-nano`; otherwise use `-Provider mock` for the normal
  deterministic acceptance path. A missing live key must be reported safely,
  never shown.

- Local Cookbook data and uploads are disposable and live under ignored
  `.local/vanilla-cookbook/`; do not use production database or upload paths.

- For a separate, manually authorized live acceptance, use the no-argument
  launcher and first confirm its safe summary reports `openai` and
  `gpt-5.4-nano`. Run one minimal importer request only within the configured
  budget/token cap. Do not use the Playwright runner for this path: it
  intentionally refuses non-mock sidecars.

## Product checks

- Readiness shows provider mode/model, saved-recipe fixture status, dataset
  fixture status, and the mock/offline default.
- At normal desktop width, readiness, action cards, and guidance are clearly
  separated; action buttons remain inside their cards with no horizontal scroll.
- If a fixture is missing, restart `start-ai-demo-local.ps1`; do not add raw
  datasets to the repository.
- **Open Cookbook** uses `COOKBOOK_TARGET_URL` when set; otherwise it redirects
  to the local upstream app at `http://127.0.0.1:3000/`. If the local target is
  unavailable, start Docker Compose and refresh the product page. An exposed
  deployment should use its configured public Cookbook URL.
- **Open AI Recipe Creator** opens `/demo`, where importer, Ask My Cookbook,
  Dataset, Meal Planner, and Recipe Session Alpha remain available.
- Confirm the selected AI mode is carried into each generated workflow:
  mock mode reports `mock/mock-basic`; an unconfigured Live OpenAI selection
  reports a safe unavailable message instead of a disguised mock response.

- The local Cookbook container must be running for the handoff to be useful;
  if it is not, the sidecar remains healthy and the product page gives the
  Compose recovery instruction.

## Recipe Session Alpha checks

- Start a detailed cheesecake request and verify a draft with citations.
- Start `make dessert` and verify exactly one clarification question.
- Send `actually make it no-bake` after a baked draft and verify RAG refresh
  plus a revision summary.
- Send `thanks` and verify no RAG refresh; existing draft/citations are reused.
- Finalize for demo and verify the explicit demo-only, no-production-writeback
  warning.

## Safety and go/no-go

- Mock/offline mode is the normal acceptance path; do not enable live OpenAI.
- Live OpenAI is available only with explicit opt-in, an approved
  `gpt-5.4-nano` configuration, and existing budget limits; browser selection
  alone never enables a live call.
- Local live product mode defaults to 500 output tokens and accepts an explicit
  500..1000 inclusive; 1000 is a ceiling, not the recommended default. Values
  below 500 or above 1000 fail before startup.
- Product and readiness content must not expose secrets, prompts, provider
  responses, environment values, or local paths.
- Direct Windows pytest may fail on the known `pytest-of-scott` Temp ACL issue;
  use the Git Bash validator as the reliable full-suite check when it passes.
- Optional local UI QA can run the Playwright troubleshooting harness against a
  separately started mock sidecar; traces, screenshots, reports, and videos
  remain ignored and live OpenAI is not required.
- If a live importer returns 503, run the no-call preflight with
  `scripts/diagnose-live-importer.ps1`. Only an explicitly approved operator
  may add `-ApproveLiveCall`; the diagnostic makes one importer call at most
  and records only a safe category/guidance result.
- If startup reports port 8000 in use, inspect `netstat -ano | findstr :8000`
  and stop only an old sidecar you recognize. Never auto-kill an unknown
  process. Align or clear inherited `AI_MODEL`/`OPENAI_MODEL` values when the
  preflight reports `model_not_allowed`.
- Treat `output_cap_or_incomplete_response` as a reached-but-incomplete live
  response, not a configuration failure. Do not retry repeatedly; any cap or
  timeout adjustment is a separately approved one-call follow-up.
- The explicit manual `openai` / `gpt-5.4-nano` importer diagnostic passed at
  500 and 1000 output tokens. Use `-MaxOutputTokens 500` as the recommended
  manual acceptance cap.
- The 400-token run failed safely with
  `output_cap_or_incomplete_response` / `JSONDecodeError`; the earlier
  300-token run was also too low for complete strict-schema JSON. A 1000-token
  cap remains a troubleshooting ceiling, not the recommended default.
- Preflight is required before approval; each approved invocation permits
  exactly one bounded importer call and never retries. Normal validation remains
  mock/offline and does not call live OpenAI.
- Go for AWS/platform planning only when `/product`, redirects, readiness,
  Recipe Session Alpha flows, mock smoke, and offline validation all pass.
- No-go if the shell cannot guide an operator to recovery, fixture state is
  unsafe, redirects are wrong, or any production/public boundary is crossed.
