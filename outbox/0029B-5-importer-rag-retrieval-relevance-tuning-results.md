# 0029B-5 Importer RAG Retrieval Relevance Tuning

Status: complete.

## Summary

Improved importer retrieval so dish-specific examples outrank broad category matches, added weak-match warnings and retrieval metadata, and updated the demo UI and docs to surface the new signals safely.

This stays inside the current offline-first demo boundary. It does not add production auth, billing, public live AI exposure, migrations, route changes, vector storage, embeddings, or raw dataset commits.

## Problem Observed

The importer was functionally working, but retrieval could still drift toward broad dessert or pasta neighbors instead of the intended dish.

Example:

- cheesecake queries could surface apple crumble, pear cake, and poached pears as the cited examples;
- those were adjacent by category, but not specific enough to support a strong RAG claim.

## Retrieval Relevance Changes

- Added anchor-aware query analysis in `ai-api/app/dataset_index.py`.
- Boosted exact dish-name matches and core ingredient / method anchors.
- Downweighted broad terms like cream, sugar, cheese, bake, dessert, chicken, dinner, pasta, and rice when they appear without stronger dish intent.
- Added importer retrieval metadata:
  - query;
  - anchors used;
  - matched result IDs;
  - matched result scores;
  - dataset limit;
  - document count via the existing index summary;
  - relevance category;
  - weak-match warning when appropriate.
- Added weak-retrieval warnings when retrieved examples are not materially specific enough.
- Updated the importer prompt so weak retrieved examples are treated as structure-only guidance.

## Observed Manual Results

I validated the ranking behavior with a direct local Python harness against a small fixture dataset with distractor recipes.

Observed results:

- cheesecake ranked above apple crumble / pear cake / poached pear distractors;
- carbonara ranked above creamy pasta distractors;
- omelet ranked above breakfast/toast distractors;
- chicken and rice casserole ranked above chicken-only and rice-only distractors;
- weak cheesecake-only-distractor data produced a weak-match warning.

The live OpenAI path was not used for this task.

## Tests Added

- Deterministic importer retrieval ranking tests for:
  - cheesecake;
  - carbonara;
  - omelet;
  - chicken and rice casserole.
- Importer metadata tests for strong matches.
- Importer weak-match warning tests for distractor-only retrieval.
- Demo UI static-asset assertions for the new retrieval metadata fields.
- Existing importer tests now assert the new retrieval metadata behaves as expected.

## Validation Results

Ran the requested offline validation set:

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` -> passed `17/17`
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` -> failed on this Windows environment with the known temp-directory ACL issue under `C:\Users\scott\AppData\Local\Temp\pytest-of-scott`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` -> passed `144` pytest cases and `17` offline eval cases
- `git diff --check` -> passed
- `docker compose config --quiet` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` -> skipped cleanly without opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` -> skipped cleanly without opt-in

## Live OpenAI

Live OpenAI was skipped during normal validation.

## Remaining Limitations

- Retrieval is still deterministic keyword/anchor scoring rather than embeddings.
- The fixture dataset remains small unless the operator points the demo at the full `recipe-dataset` path.
- Weak-match warnings are heuristic; they are good enough for the current demo boundary, but not a substitute for semantic retrieval.

## Recommended Next Task

Move to the next planned architecture or access-control task in the `0029C` line.

## Artifact Safety

No `.tmp-ai-demo/` artifacts, raw response JSON, API keys, env files, raw datasets, screenshots, logs, credentials, or generated live artifacts were committed.
