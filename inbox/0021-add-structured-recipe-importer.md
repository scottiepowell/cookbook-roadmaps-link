# Task 0021: Add Structured Recipe Importer

Add a structured recipe importer to the `ai-api` sidecar using the existing provider harness. The importer must use the mock provider by default for tests and validation. Do not run live OpenAI calls during automated validation. OpenAI `gpt-5.4-nano` may be supported only as an optional/manual provider path through the existing `OPENAI_API_KEY` and `OPENAI_ENABLE_LIVE_TESTS` settings.

Implement a new endpoint that accepts messy pasted recipe text and returns validated structured recipe draft JSON. This is an importer draft only: do not write to the Vanilla Cookbook database, do not modify recipes, do not add RAG, do not add embeddings, do not add meal planning, and do not add shopping-list generation.

Expected work:

- Add recipe import schemas with Pydantic.
- Add importer service logic under `ai-api/app/`.
- Add FastAPI endpoint for structured recipe import.
- Use `provider.generate_structured(...)` from the 0019 provider harness.
- Validate provider output before returning it.
- Add deterministic offline tests using the mock provider.
- Add tests for invalid/empty recipe text.
- Add tests proving no database write-back happens.
- Add docs explaining mock/default behavior and optional OpenAI nano manual testing.
- Update README/docs/repo-map/backlog where appropriate.
- Run validation.
- Write `outbox/0021-add-structured-recipe-importer-results.md`.
- Commit and push.

Important constraints:

- Mock remains the default provider.
- No live OpenAI calls in CI or normal validation.
- Do not print, log, return, or document `OPENAI_API_KEY`.
- Do not commit `.env`.
- Do not change deployment behavior.
- Do not change existing search behavior.
- Do not change the Windows line-ending fix from task 0020.

Run:

- `python -m pytest ai-api\tests`
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`
- `git diff --check`
- `docker compose config --quiet`

Commit message:

```text
mailbox: complete task 0021 add structured recipe importer
```
