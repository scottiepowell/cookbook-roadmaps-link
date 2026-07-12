Title: 0030P No-Bake Cheesecake Importer Session Regression Fix Results

Summary

- Fixed the recipe-session clarification regression where `cooking_method=no-bake` was captured correctly but the generated draft still used baked cheesecake instructions.
- Kept the fix on the 0030 baseline only. No GLM, secondary-provider, provider-selection, auth, storage, billing, or public-route behavior was added.

Manual Bug Summary

- Failing path:
  - `start: make dessert`
  - `message: cheesecake, no-bake, for 4 people`
- The session state correctly captured:
  - `dish_intent=cheesecake`
  - `serving_count=4`
  - `cooking_method=no-bake`
- The generated draft still contained baked-only cheesecake steps such as `preheat`, `oven`, and `bake`.

Root Cause

- `ai-api/app/importer.py` post-processed any draft whose source text contained `cheesecake` into a baked cheesecake instruction template.
- That branch did not guard against explicit no-bake constraints like `no-bake` or `no bake`.

Importer Fix

- Added a `_requests_no_bake(text)` helper in `ai-api/app/importer.py`.
- The helper recognizes explicit no-bake variants:
  - `no-bake`
  - `no bake`
  - `no oven`
  - `without baking`
  - `do not bake`
  - `don't bake`
  - `chilled cheesecake`
  - `refrigerator cheesecake`
- Updated cheesecake draft shaping to follow this order:
  - if cheesecake and explicit no-bake signal: generate chill/refrigerate/serve-cold instructions
  - else if cheesecake: keep baked cheesecake instructions
- Updated importer guidance text so baked and no-bake cheesecake constraints are both explicit.

Session Regression Coverage

- Strengthened `ai-api/tests/test_recipe_session_api.py` for the exact clarification flow:
  - `start: make dessert`
  - `message: cheesecake, no-bake, for 4 people`
- Added assertions that:
  - `response_state` is `rag_refreshed` or `draft_revised`
  - `requirements.dish_intent.value == cheesecake`
  - `requirements.cooking_method.value == no-bake`
  - `resolved_questions` is populated
  - `open_questions` is empty
  - retrieval query contains `no-bake` or `no bake`
  - draft instructions include chill/refrigerate/serve-cold behavior
  - draft instructions do not include `preheat`, `oven`, `bake`, or `center is just set`

Importer Regression Coverage

- Added direct importer tests in `ai-api/tests/test_importer.py`.
- Added a dedicated validation-target file `ai-api/tests/test_import_recipe.py` so the requested pytest command exists and covers:
  - `cheesecake, no-bake, for 4 people`
  - explicit baked cheesecake input
- Assertions verify:
  - no-bake drafts mention chill/refrigerate/serve cold
  - no-bake drafts do not mention baked-only terms
  - explicit baked cheesecake still keeps baked behavior

Offline Eval Harness Coverage

- Updated `evals/ai_cookbook/session_cases.yaml` and `evals/ai_cookbook/session_eval.py`.
- The session eval harness now checks the no-bake clarification path for:
  - retrieval query preservation of the no-bake method signal
  - resolved/open question expectations
  - required draft terms
  - forbidden baked-only draft terms
- This means `run_evals.py` now fails if the session API keeps the right requirement state but the draft regresses back to baked cheesecake behavior.

Docs Updated

- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`

The runbook now explicitly documents the regression case:

- `make dessert -> cheesecake, no-bake, for 4 people`

It also states that no-bake constraints must survive:

- clarification
- retrieval query building
- importer draft shaping
- finalize/demo display

Validation Results

- `python -m pytest ai-api/tests/test_import_recipe.py -q`: passed
- `python evals/ai_cookbook/run_evals.py`: passed
- `python scripts/e2e-ai-29-30-regression.py`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-ai-env-file-loader.ps1`: passed
- `bash scripts/validate-repo.sh`: passed
- `git diff --check`: passed
- `docker compose config --quiet`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1`: skipped cleanly without live opt-in

Windows Pytest Note

- Direct Windows `pytest ai-api/tests/test_recipe_session_api.py -q` hit the known local `pytest-of-scott` temp ACL issue before test execution.
- The Git Bash repository validator path passed the full AI API suite, including `ai-api/tests/test_recipe_session_api.py` and the new no-bake regression assertions.

Non-Goals

- No GLM provider integration
- No secondary-provider routing
- No provider selection changes
- No model fallback changes
- No public route exposure
- No Cloudflare or DNS changes
- No production auth
- No durable storage
- No Redis, Postgres, or SQLite persistence changes
- No paid access, payment integration, ads, or sponsor runtime behavior
- No live OpenAI calls added to normal validation

Artifact Safety Confirmation

- No `.env` files committed
- No provider keys committed
- No raw provider prompts committed
- No raw provider responses committed
- No `.tmp-ai-demo` artifacts committed
- No logs or screenshots committed
- No local absolute paths added to public docs examples

Recommendation

- `0031A` can continue after this baseline fix.
- Future secondary-provider or offload comparisons should use this corrected no-bake cheesecake session behavior as part of the stable 0030 baseline.
