# 0030I-6 Results: Local Live Runtime Profile and Secret Injection

## Local runtime behavior

`scripts/start-ai-demo-local.ps1` now automatically looks for ignored local
`.env` and imports missing process values before it resolves the sidecar
runtime. A valid local live configuration starts OpenAI mode with only
`gpt-5.4-nano`, a 1–300 output-token cap, and a 1–25 cent live-test budget.
No separate JSON profile was added: the existing env-file helper provides the
smallest reliable local profile format.

Use the normal command after configuring ignored `.env`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

`-WriteMissingLiveDefaults` can append safe non-secret defaults to `.env`.
It deliberately never writes `OPENAI_API_KEY`, and prints guidance to add that
value only to ignored `.env` or the local process environment. `-Provider mock`
remains an explicit deterministic override. `-CheckRuntimeProfile` provides a
safe no-server summary for local setup checks.

## Secret injection and precedence

The launcher imports ignored local values into its PowerShell process, then
starts Uvicorn as a child that inherits those server-side environment values.
The browser receives only safe mode/model preferences; keys are not placed in
URLs, request bodies, browser storage, static assets, committed files, or
startup output. The summary prints only `redacted-present` or `missing` for
the key.

Precedence is: explicit script argument, existing process environment, local
ignored `.env`, then script default. Browser selection still cannot bypass the
server's existing live opt-in, key, provider-budget, or request routing checks.
Future production deployment should use a managed secret store or deployment
secret mechanism rather than local env files.

## Tests and validation

- Added deterministic launcher tests using temporary fake env files only:
  automatic live resolution, safe key redaction, missing-key guidance, mock
  override, safe-default initialization, `.env` ignore rules, and secret-free
  example values.
- `scripts/test-ai-env-file-loader.ps1`: passed, 5/5.
- `scripts/validate-repo.sh`: passed, 337 pytest tests; offline eval coverage
  remained enabled and mock-only.
- `scripts/demo-ai-mock.ps1`: passed; offline evals passed 39/39 and endpoint
  smoke remained explicitly `mock/mock-basic`.
- `git diff --check` and `docker compose config --quiet`: passed.
- Live smoke and live-eval wrappers skipped cleanly without explicit opt-in.
  No live OpenAI call was made.

## Non-goals

No production secret store, AWS/platform work, deployment automation, public
routes, auth, payment, Cloudflare/DNS change, secondary-provider runtime,
embeddings/vector database, upstream UI rewrite, browser automation, raw
datasets, persistent index, or disk cache was added.

## Follow-up correction

The completed local Playwright hardening identified that an explicit mock
launcher process must not inherit live enablement from ignored `.env`. The
launcher now forces `OPENAI_ENABLE_LIVE_TESTS=false` and `AI_MODEL=mock-basic`
for `-Provider mock`; the normal no-argument launch still resolves valid local
live configuration from ignored `.env`. The safe defaults and `.env.example`
now set both `AI_MODEL` and `OPENAI_MODEL` to `gpt-5.4-nano` for live mode.

Validation after this correction: the offline Git Bash validator passed 338
pytest tests and the 39-case eval suite; mock smoke remained mock-only. Live
wrappers were not run with the ignored live configuration, so no live provider
call was made for this correction.
