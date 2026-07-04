# Task 0022: Add RAG Ask Endpoint

## Goal

Add the first retrieval-augmented question-answering endpoint to the `ai-api` sidecar.

The endpoint should answer questions over saved recipe documents by retrieving relevant recipes first, then asking the provider harness to synthesize a grounded answer from only those retrieved recipes.

This task builds on:

- `0017`: read-only recipe reader
- `0018`: deterministic recipe search API
- `0019`: provider harness with mock default and OpenAI nano path
- `0021`: structured recipe importer

## Endpoint

Add:

```text
POST /ai/ask
```

Suggested request:

```json
{
  "question": "What seafood soup can I make with smoked haddock and potatoes?",
  "limit": 5
}
```

Suggested response:

```json
{
  "answer": "Based on your saved recipes, Fresh and Smoked Seafood Chowder is a good match because it uses smoked haddock, firm white fish, mussels, potatoes, milk, and cream.",
  "citations": [
    {
      "recipe_id": "1",
      "title": "Fresh and Smoked Seafood Chowder",
      "snippet": "...smoked haddock...potatoes..."
    }
  ],
  "provider": "mock",
  "model": "mock-basic",
  "retrieval": {
    "query": "seafood soup smoked haddock potatoes",
    "count": 1
  },
  "warnings": []
}
```

The exact field names may differ if they fit existing project schemas better, but the response must include an answer, citations, provider/model metadata, and retrieval metadata.

## Required Behavior

1. Use deterministic retrieval before any provider call.

   Use the existing recipe reader and search functionality from tasks 0017/0018. Do not send the whole recipe database/corpus to the provider.

2. The provider must only receive retrieved recipe context.

   The prompt should include:

   - user question
   - top retrieved recipe titles/IDs/snippets/ingredients/instructions as available
   - instruction to answer only from provided recipe context
   - instruction to cite recipe IDs/titles
   - instruction to say it does not know when the retrieved context is insufficient

3. Mock provider remains the default.

   Automated tests and validation must use mock/offline behavior only.

4. OpenAI remains optional/manual only.

   Do not run live OpenAI calls during validation. OpenAI `gpt-5.4-nano` may remain available through the existing provider harness for later manual smoke testing only.

5. No-match behavior must be safe.

   If no recipes are retrieved, return a controlled no-match answer without calling the provider, or call only the mock provider if that is easier to keep architecture consistent. The answer must not invent recipes.

6. Answers must be grounded.

   The response must include citations for any recipe-specific recommendation. If citations are missing, the endpoint behavior/tests should fail.

7. Secrets must not leak.

   Do not return, log, print, or document provider keys, token fragments, raw `.env` values, or Authorization headers.

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/rag.py
ai-api/app/schemas.py
ai-api/app/main.py
ai-api/tests/test_rag.py
ai-api/tests/test_ai_ask_api.py
docs/rag-ask-endpoint.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/ai-evals-plan.md
docs/repo-map.md
ai-api/README.md
outbox/0022-add-rag-ask-endpoint-results.md
```

Keep the implementation simple and local. Do not create embeddings or a vector database in this task.

## Schema Guidance

Add Pydantic schemas for:

- ask request
- citation object
- retrieval metadata
- ask response

At minimum:

```text
AskRecipeRequest
AskRecipeCitation
AskRecipeRetrieval
AskRecipeResponse
```

The request should validate:

- non-empty question
- reasonable limit, such as 1-10

The response should include:

- answer
- citations
- provider
- model
- retrieval metadata
- warnings
- optional usage

## Prompt Construction

The RAG service should build a small context payload from retrieved recipes.

Do include:

- recipe ID
- title
- matched snippet/reasons if available
- ingredients/instructions/summary fields if available from `RecipeDocument`

Do not include:

- all recipes
- secrets
- `.env` values
- raw provider config
- private filesystem paths unless needed for debugging and safe

Suggested system instruction:

```text
You answer questions only from the provided saved recipe context. If the answer is not supported by the context, say you do not know based on the saved recipes. Cite recipe IDs and titles for recipe-specific claims. Do not invent recipes, ingredients, or instructions.
```

## Tests

Add deterministic offline tests for:

1. Empty/blank question is rejected.
2. Search/retrieval runs before provider answer generation.
3. Endpoint returns an answer and citations for a matching recipe fixture.
4. No-match question returns a controlled no-match response and does not invent a recipe.
5. Response does not include `OPENAI_API_KEY`, `sk-`, or secret-like values.
6. Provider metadata is returned safely.
7. Existing health, config, provider, reader, search, and importer tests still pass.
8. No database write-back occurs.

Use generated SQLite fixtures or existing fixture patterns. Do not require the real cookbook database.

## Non-Goals

Do not implement:

- embeddings
- vector database
- semantic search
- meal planner
- shopping list
- bulk ebook ingestion
- recipe write-back
- UI changes
- Cloudflare route changes
- deployment changes
- live OpenAI validation
- Anthropic/Gemini/Ollama real providers

## Validation

Run from Windows PowerShell in the repo:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
python -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If any command is unavailable, document it in the outbox report.

## Outbox Report

Create:

```text
outbox/0022-add-rag-ask-endpoint-results.md
```

Include:

- Summary
- Files changed
- Endpoint added
- Retrieval behavior
- Provider behavior
- No-match behavior
- Citation behavior
- Validation results
- Confirmation that no live OpenAI calls were run
- Confirmation that no `.env` or secrets were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add ai-api docs README.md outbox/0022-add-rag-ask-endpoint-results.md
git commit -m "mailbox: complete task 0022 add rag ask endpoint"
git push origin main
```

## Done Criteria

- `POST /ai/ask` exists.
- Request/response schemas exist.
- Retrieval runs before provider generation.
- Provider receives only retrieved recipe context.
- Mock provider works by default.
- No live OpenAI calls are required.
- Matching answers include citations.
- No-match answers do not invent recipes.
- No recipe write-back occurs.
- No secrets are exposed.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
