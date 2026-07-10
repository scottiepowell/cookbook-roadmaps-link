# 0030E Recipe Session Eval Harness And Regression Baseline Results

## Summary

Added a deterministic offline/mock recipe-session eval harness and integrated it into `evals/ai_cookbook/run_evals.py` as the `recipe_session` group.

## Eval Case File Added

Created `evals/ai_cookbook/session_cases.yaml` with eight regression cases:

- detailed cheesecake start generates a draft;
- vague dessert start asks one clarification;
- no-bake method follow-up refreshes RAG;
- carbonara chatter does not refresh RAG;
- omelet formatting-only follow-up does not refresh RAG;
- clarification answer generates a draft;
- finalize is demo-only;
- unknown session ID returns safe not-found behavior.

## Eval Runner Added

Created `evals/ai_cookbook/session_eval.py`.

The runner:

- uses FastAPI `TestClient`;
- forces mock provider settings;
- writes generated dataset fixtures only;
- clears the bounded recipe-session store between cases;
- resets retrieval cache between cases;
- exercises start/message/get/finalize flows;
- returns readable pass/fail summaries with case IDs and elapsed time;
- fails on expected-state, refresh, draft, citation, or safety regressions.

## `run_evals.py` Integration

`evals/ai_cookbook/run_evals.py` now loads session cases and prints progress such as:

```text
EVAL: starting recipe_session: vague_dessert_clarifies
PASS: vague_dessert_clarifies state=clarification_needed elapsed=0.00s
```

The offline eval baseline now reports 36 passing cases.

## Safety Checks

Each session eval response is checked for forbidden content including:

- provider key markers;
- authorization markers;
- environment file markers;
- raw prompt/provider-response markers;
- stack traces;
- local absolute Windows or Unix path markers;
- generated dataset directory path;
- production storage write-back path indicators.

## Tests Added

Added `ai-api/tests/test_recipe_session_eval_harness.py` covering:

- case fixture loading and required IDs;
- all session eval cases passing with generated fixture data;
- failure summaries including the case ID and expected state;
- independence from live provider environment settings.

## Validation Results

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_recipe_session_eval_harness.py` - passed, 4 tests.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` - passed, 36/36 offline evals.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` - passed, including 214 pytest tests and 36 offline evals.
- `git diff --check` - passed.
- `docker compose config --quiet` - passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` - passed, including 36 offline evals and endpoint smoke checks.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` - skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` - skipped cleanly without live opt-in.

## Explicit Non-Goals

No production storage, database migrations, auth, paid access, public route exposure, Cloudflare changes, persistent user memory, Redis, Postgres, SQLite session persistence, vector DB, embeddings, Qdrant, pgvector, full chat UI, browser automation, screenshots, or live OpenAI calls were added.

## Artifact Safety Confirmation

The harness uses generated fixture data only and does not require the real `recipe-dataset/` folder. No raw dataset files, generated live artifacts, screenshots, logs, credentials, environment files, raw provider prompts, generated persistent indexes, disk cache, or production session storage are intended for commit.
