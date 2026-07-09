# 0029B-9 RAG Honesty And Citation Support Policy Results

## Summary
Implemented a deterministic RAG support policy for the recipe importer so the API and demo UI can say whether retrieved dataset examples were strongly, moderately, weakly, or not at all supportive of a generated recipe.

## Observed Manual Results
- The importer path still returned 200 for the RAG-informed recipe workflows in offline validation.
- Strong dish-specific retrieval stayed intact for cheesecake, carbonara, omelet, and chicken/rice casserole queries.
- The UI now shows an explicit RAG support label and a short support message alongside importer citations and retrieval metadata.

## Support Policy Changes
- Added `ai-api/app/rag_support_policy.py` with deterministic support classification.
- Support levels are limited to `strong`, `moderate`, `weak`, and `none`.
- Added safe support metadata to `RecipeImportRetrievalMetadata`:
  - `support_level`
  - `support_reason`
  - `citation_support_count`
  - `weak_citation_count`
  - `strong_citation_count`
  - `support_message`
  - `should_claim_rag_grounded`
  - `should_show_weak_support_warning`
- Updated importer prompt guidance to use the support message without exposing raw policy internals.

## Citation Rendering Fix
- Updated the demo UI importer panel so moderate and weak citations are labeled as partial or broad examples instead of authoritative sources.
- The UI now surfaces the support label, support message, and safe support metadata near the citations and retrieval section.

## Retrieval Evaluation Changes
- Extended the offline retrieval harness so support level is tracked alongside ranking quality.
- Retrieval eval cases can assert an expected support level.
- Added deterministic support-policy unit tests for strong, moderate, weak, and none.

## Tests Added
- Support policy unit tests for all four support levels.
- Importer tests that verify support metadata is present in the API response.
- Importer relevance tests that verify strong and weak support classifications.
- Demo UI static tests that verify support messaging and honest citation labels are present.
- Retrieval harness tests that verify support expectations are carried through the offline eval path.

## Validation Results
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` hit the known Windows temp-directory ACL issue.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed, including 163 pytest cases.
- `git diff --check` passed.
- `docker compose config --quiet` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly because live opt-in was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly because live opt-in was not set.

## Live OpenAI
- Live OpenAI was not run during normal validation.

## Recommended Next Task
- `0029C: Session And Metering Schema Draft`

## Artifact Safety
- No raw dataset files were committed.
- No generated live artifacts were committed.
- No `.tmp-ai-demo/` artifacts, secrets, env files, logs, screenshots, credentials, raw prompts, or raw provider responses were committed.
