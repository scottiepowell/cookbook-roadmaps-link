# Local Cookbook AI Product Acceptance Checklist

## Prerequisites and start

- Use the repository virtual environment and Docker Compose when the upstream
  Cookbook container is needed.
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
- **Open Cookbook** redirects to the local upstream app on port 3000.
- **Open AI Recipe Creator** opens `/demo`, where importer, Ask My Cookbook,
  Dataset, Meal Planner, and Recipe Session Alpha remain available.
- Confirm the selected AI mode is carried into each generated workflow:
  mock mode reports `mock/mock-basic`; an unconfigured Live OpenAI selection
  reports a safe unavailable message instead of a disguised mock response.

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
- The bounded diagnostic uses a tiny scrambled-egg fixture and defaults to a
  300-token cap; the recorded 300-token live diagnostic still failed with
  `output_cap_or_incomplete_response`.
- A 1000-token cap is an explicit manual diagnostic only. Use the preflight
  and approval commands with `-MaxOutputTokens 1000`; this permits one approved
  importer call per operator run, with no repeated retries. Normal validation
  remains mock/offline. If it succeeds, dial down manually:
  `1000 -> 800 -> 600 -> 500 -> 400 -> 300`.
- Go for AWS/platform planning only when `/product`, redirects, readiness,
  Recipe Session Alpha flows, mock smoke, and offline validation all pass.
- No-go if the shell cannot guide an operator to recovery, fixture state is
  unsafe, redirects are wrong, or any production/public boundary is crossed.
