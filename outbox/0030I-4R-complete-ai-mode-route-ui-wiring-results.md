# 0030I-4R Results: Complete AI Mode Route/UI Wiring

## Finding and correction

`0030I-4` was incomplete: the shared resolver and request fields existed, but
the supported routes did not consistently invoke the resolver and `/demo`
defined its selector helper without attaching it to every generated-workflow
payload. The partial working-tree corrections were preserved and completed.

The observed importer `503` was expected safe live-unavailable behavior, not a
mock regression. A UI alias defect caused an older persisted `live` value to
be sent with `mock-basic`; the resolver correctly rejected that unsafe
combination. `/demo` now normalizes `live`/`openai` to
`openai/gpt-5.4-nano` and `mock`/`offline` to `mock/mock-basic` before every
provider-backed request.

## Completed wiring

- Request-scoped mode resolution and provider injection now cover importer,
  Ask My Cookbook, Dataset Ask, Meal Planner, Recipe Session start, and
  Recipe Session generation follow-ups.
- Explicit mock requests use `mock/mock-basic` across those workflows.
- Explicit unavailable live requests receive a controlled safe `503`; they do
  not fall back to successful mock output while claiming live behavior.
- Recipe Session responses now retain safe effective provider/model metadata
  for generated drafts and revisions.
- Legacy callers with no provider preference retain their existing
  process-configured provider and budget behavior; browser requests do not
  mutate global provider settings.
- `/demo` attaches normalized selector state to importer, Recipe Session
  start/message, Ask, Dataset Ask, and Meal Planner payloads.

## Regression and smoke coverage

- Added HTTP routing tests for explicit mock routing, unavailable live routing,
  invalid provider/model combinations, response safety, and Recipe Session
  generation metadata.
- Added static UI assertions for alias normalization and all six selector
  payload attachments.
- Updated mock smoke to explicitly send `provider_mode=mock` and
  `model=mock-basic`, then assert `mock/mock-basic` for importer, Ask,
  Dataset Ask, Meal Planner, Recipe Session start, and Recipe Session
  follow-up generation.
- Future-dated a time-sensitive usage-report test fixture so its intended
  active-session assertion remains valid after July 2026.

## Validation

- `scripts/validate-repo.sh`: passed, including **333 pytest tests** and the
  offline eval suite.
- `scripts/demo-ai-mock.ps1`: passed; offline evals passed **39/39** and the
  explicit mock endpoint smoke passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- Live smoke and live eval wrappers skipped cleanly because explicit live
  opt-in was absent. No live OpenAI call was made.

## Non-goals

No AWS/platform work, auth, public exposure, production storage, provider
routing overhaul, arbitrary model selection, embeddings/vector storage,
browser automation, screenshots, raw datasets, or disk cache were added.

All stated `0030I-4R` acceptance criteria are now covered; `0030I-5` may run
as its separate follow-on audit task.
