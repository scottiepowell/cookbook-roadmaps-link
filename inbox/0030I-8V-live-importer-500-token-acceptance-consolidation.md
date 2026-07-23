# 0030I-8V Live Importer 500-Token Acceptance Consolidation

## Goal

Consolidate post-task operator evidence showing that the explicit manual live
importer diagnostic succeeds at 500 output tokens and fails safely at 400 output
tokens. Update docs/status so 500 tokens is treated as the current observed
manual live importer acceptance cap, while normal validation remains mock/offline.

## Context

The 0030I-8U task added an approval-gated `-MaxOutputTokens` override for the
live importer diagnostic. The task itself made no live OpenAI call.

After 0030I-8U was pushed, the operator ran bounded live diagnostics:

- `-MaxOutputTokens 1000`: passed.
- `-MaxOutputTokens 500`: passed.
- `-MaxOutputTokens 400`: failed safely with
  `output_cap_or_incomplete_response` and `JSONDecodeError`.

This indicates that 500 tokens is the current observed floor for the explicit
manual diagnostic profile, while 400 tokens is too low for complete schema JSON
with the current importer prompt/schema path.

## Requirements

- Do not create a new task.
- Do not run live OpenAI during normal validation.
- Do not expose secrets or raw provider output.
- Do not add retries.
- Do not weaken strict schema validation.
- Do not accept invalid or incomplete JSON as success.
- Do not change normal mock/offline validation behavior.
- Do not start AWS/platform work.

## Implementation guidance

Update docs and status files to say:

- successful live importer acceptance is now proven for the explicit manual
  `openai` / `gpt-5.4-nano` diagnostic profile at 500 output tokens;
- 1000 tokens remains the manual troubleshooting ceiling, not the recommended
  default acceptance cap;
- 400 tokens and the previous 300-token profile are too low for the current
  strict schema JSON importer path;
- normal validation remains mock/offline and should not call live OpenAI;
- live importer acceptance requires explicit operator approval and exactly one
  bounded call per invocation.

Do not hardcode broad product defaults to 500 unless the current architecture
already clearly separates manual diagnostic defaults from product runtime caps.
Prefer documenting and wiring the recommended manual diagnostic cap only.

## Files likely touched

- `README.md`
- `docs/ai-live-demo-runbook.md`
- `docs/live-openai-smoke-tests.md`
- `docs/local-product-acceptance-checklist.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `outbox/0030I-8V-live-importer-500-token-acceptance-consolidation-results.md`

## Tests

Add or update deterministic tests only if implementation changes are needed.
If this is docs/status-only, no new tests are required beyond normal validation.

If code changes are made, cover:

- recommended manual cap is 500;
- 1000 remains allowed as an explicit troubleshooting upper bound;
- values above 1000 remain rejected;
- preflight remains no-call;
- approved live diagnostic remains one call per invocation;
- no secrets/raw provider output are emitted.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

Live wrappers should skip unless explicitly opted in.

## Outbox

Create:

```text
outbox/0030I-8V-live-importer-500-token-acceptance-consolidation-results.md
```

Summarize:

- the 1000-token pass;
- the 500-token pass;
- the 400-token safe failure;
- recommended manual live importer acceptance cap;
- normal validation boundary;
- validation results;
- explicit non-goals.

## Commit

```bash
git add docs README.md outbox/0030I-8V-live-importer-500-token-acceptance-consolidation-results.md
git commit -m "mailbox: complete task 0030I-8V live importer token cap consolidation"
git pull --rebase origin main
git push origin main
```
