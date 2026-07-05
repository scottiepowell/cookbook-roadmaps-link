# AI Cookbook Offline Evals

These evals run offline against tiny generated fixtures. They use the mock provider by default and do not require the real Kaggle dataset, network access, Docker, OpenAI keys, or live providers.

Run locally:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

The repository validator also runs this eval harness after the AI API pytest suite.

The current cases focus on dataset ask grounding, citation completeness, no-match behavior, missing-dataset behavior, invented/non-retrieved source IDs where detectable, and secret-like response leakage.
