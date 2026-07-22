# Playwright UI Troubleshooting

This optional local-only harness checks the real browser behavior of the
Cookbook AI product shell and workspace. It supplements backend pytest, mock
smoke, and offline evals; it is not part of normal repository validation and
never requires live OpenAI.

## Setup and run

```powershell
npm install
npx playwright install chromium

# Terminal one: force the safe local server mode.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock

# Terminal two
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

The runner requires `http://127.0.0.1:8000/product` to be available and gives
concise recovery guidance when it is not. It does not start the sidecar or
enable live mode for you. It additionally checks `/demo/readiness` and refuses
to run unless the sidecar reports `mock`/`mock-basic`; an explicit
`-Provider mock` launcher override disables inherited live enablement for that
child process.

It intentionally refuses a live-capable sidecar. Use it to prove mock payload
propagation and controlled live-unavailable UI behavior, not to make a live
acceptance call. A manually authorized live acceptance begins with the
no-argument launcher and remains server-side/budget-gated.

## What it checks

- `/product` visibility, action-card bounds, desktop overflow, and local route
  behavior;
- `/product` to `/demo` mode propagation through `cookbook-ai-mode`;
- normalization of stale `live`/`offline` aliases to the approved
  `openai/gpt-5.4-nano` or `mock/mock-basic` payload;
- request payloads for importer, Recipe Session, Ask, Dataset Ask, and Meal
  Planner;
- mock success metadata and controlled live-unavailable UI behavior; and
- the visible `/demo` link back to `/product`.

The current HTTP schema calls the model field `model`; it is the equivalent of
an `ai_model` preference. The browser test rejects the earlier unsafe
`live`/`mock-basic` pairing and captures every provider-backed workflow
request. Against a mock-started server, selecting Live must result in safe
unavailable guidance, never mock output presented as a live success.

Artifacts such as traces, screenshots, videos, reports, and result folders are
ignored. Do not commit them or use them to capture secrets.

## Manual browser troubleshooting

Codex's optional Playwright Interactive Skill can help inspect a persistent
local browser session. Use it only for local troubleshooting, prefer
`127.0.0.1` over `localhost`, and do not paste secrets. High-trust sandbox
settings are a manual debugging choice, not a project requirement. The
repository harness does not depend on a Codex skill, a persistent session, or
browser automation in production.
