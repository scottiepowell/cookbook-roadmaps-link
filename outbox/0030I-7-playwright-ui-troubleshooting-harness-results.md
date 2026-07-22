# 0030I-7 Playwright UI troubleshooting harness results

## Outcome

Added a repository-local, Chromium-focused Playwright harness for troubleshooting the local Cookbook AI product shell and AI workspace. It complements the existing FastAPI tests, offline evals, and mock smoke; it does not replace them.

## Tooling and coverage

- Added `package.json`, lockfile, `playwright.config.js`, and `tests/ui/cookbook-ai-mode.spec.js`.
- Added `scripts/run-ui-playwright.ps1`, which verifies Node/npm, confirms the sidecar is already serving `http://127.0.0.1:8000/product`, and then runs the local browser tests. It never starts or opts into live OpenAI.
- Added product/demo coverage for visible mode controls and readiness, `/product` action navigation, `/demo` back navigation, desktop overflow and card-action bounds, and the local Cookbook redirect.
- Added browser request inspection for importer, Recipe Session start/follow-up, Ask My Cookbook, Dataset Ask, and Meal Planner. The harness asserts normalized mock payloads use `mock`/`mock-basic`, while live selection uses `openai`/`gpt-5.4-nano`.
- Added a stale localStorage `live` alias check and a mock-server live-selection check for controlled unavailable guidance rather than disguised mock output.
- Added a concise demo mode-status line so the persisted selection and approved model are observable in the workspace.

## Safety and local-only boundaries

- Playwright artifacts are ignored: `test-results/`, `playwright-report/`, `ui-artifacts/`, and `*.webm`.
- The harness rejects secret-like and unsafe payload markers. No browser storage, static JavaScript, or reports contain provider keys or raw provider internals.
- Documentation records Playwright as optional local UI QA, with optional persistent Codex browser-skill guidance for manual troubleshooting only. Normal validation remains mock/offline.
- No live OpenAI calls, production routing, deployment, storage, authentication, payment, AWS/platform work, screenshots, traces, videos, datasets, indexes, or disk caches were added.

## Validation

- `npm install`: passed.
- `npx playwright test --list`: passed; four Chromium troubleshooting cases are discoverable.
- `scripts/test-ai-env-file-loader.ps1`: passed (5/5).
- `evals/ai_cookbook/run_evals.py`: passed (39/39).
- `scripts/validate-repo.sh`: passed (338 pytest tests plus offline evals).
- `git diff --check` and `docker compose config --quiet`: passed.
- `scripts/demo-ai-mock.ps1`: passed with mock-only endpoint smoke.
- Live smoke and live-eval wrappers skipped cleanly because explicit live opt-in was absent.

The Chromium binary download was attempted in this environment but timed out before a browser executable became available. Consequently, a real-browser Playwright run was not claimed as passed here. On a local machine, run `npm install`, `npx playwright install chromium`, start the sidecar in mock mode, and then run `scripts/run-ui-playwright.ps1`; generated artifacts remain ignored.

## Follow-up

Run the four browser cases after Chromium is installed locally. If they reveal a real layout or interaction regression, retain only the code/test fix; do not commit generated browser artifacts.
