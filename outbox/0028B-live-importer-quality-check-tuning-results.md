# 0028B: Live Importer Quality Check Tuning Results

Status: complete.

Note: `inbox/0028B-live-importer-quality-check-tuning.md` was not present in the local checkout when this task started, so the user-provided task text was used as the acceptance source.

## Summary

Tuned live importer quality checks so useful GPT-nano structured importer responses pass when ingredient evidence is preserved in title, ingredient names, or instructions, even when `description` is absent or worded differently.

## Live Artifact Inspection

Inspected the local generated artifact at `.tmp-ai-demo/live-evals/20260708T125943Z/responses/importer.json`. The response was useful: it produced `Lemon Herb White Beans`, included white beans, olive oil, garlic, lemon juice, parsley, and toast in structured ingredients, included action-oriented instructions, and noted missing quantities/details. The failed check was brittle because it required ingredient evidence only in `description`, which was `null`.

The generated live artifact was not staged or committed.

## Files Changed

- `evals/ai_cookbook/expected_checks.py`
- `evals/ai_cookbook/live_cases.json`
- `ai-api/app/importer.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0028B-live-importer-quality-check-tuning-results.md`

## Quality Check Changes

- Replaced the description-only ingredient check with `draft should preserve at least two input ingredients across structured fields`.
- Added `description should be ingredient-grounded when present`.
- Added canonical alias evidence for:
  - white beans: `white beans`, `beans`, `bean`
  - olive oil: `olive oil`, `oil`
  - garlic: `garlic`
  - lemon: `lemon`, `lemon juice`, `citrus`
  - parsley: `parsley`, `herbs`, `herb`
  - toast: `toast`, `bread`
- Added broader generic-placeholder detection across structured fields.
- Kept unrelated-food detection, now evaluated across draft fields rather than ingredient names only.

## Prompt Guidance

Updated importer system guidance to request a one-sentence description with one or two core ingredients when possible, put missing quantities/timing in notes, and avoid unrelated ingredients.

## Tests Added

- Useful output with structured ingredient evidence but no description passes.
- Synonym/alias ingredient evidence passes.
- Unrelated ingredient output fails.
- Generic placeholder output fails.
- Truly ungrounded importer output fails.
- Existing live eval harness and input-quality provider-call avoidance tests still pass.

## Validation

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 17 cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: hit the known Windows temp ACL issue after collecting 112 tests; 74 passed and 38 setup errors all rooted in `PermissionError: [WinError 5] Access is denied` on the per-user pytest temp directory.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed; includes 112 API tests passed and 17 offline eval cases passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live eval opt-in settings were not present.

## Live OpenAI

No live OpenAI calls were run for this task.

## Known Limitations

- The tuned checks remain deterministic and alias-based; future live responses may reveal more useful synonyms to add.
- The historical generated live response artifact remains ignored local output and is not part of source control.

## Recommended Next Task

0028C: Live Eval Failure Triage And Regression Notes.

## Artifact Safety

No private env files, API keys, raw datasets, generated live results, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts were committed.
