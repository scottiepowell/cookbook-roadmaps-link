# AI Cookbook Offline Evals

These evals run offline against tiny generated fixtures. They use the mock provider or local fixture providers and do not require the real Kaggle dataset, network access, Docker, OpenAI keys, or live providers.

Run locally:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

The repository validator also runs this eval harness after the AI API pytest suite.

The current cases cover indexed dataset ask/RAG, saved-recipe Ask My Cookbook RAG, structured recipe importer validation, saved-recipe meal planning, provider config hygiene, citation completeness, no-match behavior, missing-dataset behavior, non-retrieved source leakage where detectable, and secret-like response leakage.
