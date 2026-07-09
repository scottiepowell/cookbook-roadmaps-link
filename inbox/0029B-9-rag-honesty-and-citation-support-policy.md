# 0029B-9 RAG Honesty And Citation Support Policy

## Goal

Add a clear RAG honesty and citation-support policy for the RAG-informed recipe creator/importer.

The system now has:

- anchor-aware retrieval relevance scoring;
- offline retrieval relevance evals;
- bounded RAG context packing;
- dataset normalization for deterministic RAG;
- UI display for citations, provenance, retrieval metadata, and context-packing metadata.

The next step is to make the product language honest about how much the retrieved examples actually supported the generated recipe.

## Background

Manual testing showed the recipe creator can generate useful recipes even when citations are only moderately relevant. That is acceptable product behavior, but the UI and API should not overstate the strength of RAG support.

Examples:

- If cheesecake retrieves two cheesecake examples and one broad dessert example, the system can call the RAG support strong or mostly strong, with the broad citation treated carefully.
- If omelet retrieves breakfast-adjacent records but no actual omelet records, the recipe may still be useful, but the system should not imply it was strongly grounded in retrieved omelet examples.
- If no relevant records are found, the app can still generate from user notes and default recipe structure, but it should clearly say that retrieved dataset support was weak or unavailable.

This task is about RAG honesty, citation support classification, and safe user/operator messaging. It is not about changing model providers or adding embeddings.

## Primary Objective

Create deterministic policy logic that classifies retrieval/citation support and exposes safe, clear messaging in the API and demo UI.

The policy should answer:

```text
How strongly did retrieved dataset examples support this generated recipe?
```

## Required Work

### 1. Add RAG support policy module

Create a small deterministic policy module.

Suggested location:

```text
ai-api/app/rag_support_policy.py
```

or an appropriate existing module if better.

The module should classify support based on existing retrieval metadata, such as:

- relevance category;
- retrieved count;
- citation count;
- packed count;
- weak examples included;
- matched scores;
- anchor coverage if available;
- top-k relevant count if available;
- warning states.

### 2. Define support levels

Use a small explicit support taxonomy.

Suggested support levels:

```text
strong
moderate
weak
none
```

Meaning:

- `strong`: retrieved/packed examples materially match the dish intent and core anchors;
- `moderate`: examples are partially relevant or style/category-adjacent but not perfect;
- `weak`: examples are broad, generic, or only structure-useful;
- `none`: no useful retrieval/citations are available.

### 3. Add user-facing support messages

Add concise safe messages that can be shown in the UI.

Examples:

Strong:

```text
Dataset support is strong: retrieved examples closely match the dish intent and were used for structure, proportions, and step completeness.
```

Moderate:

```text
Dataset support is moderate: retrieved examples are related, but the draft is primarily guided by your notes and general recipe structure.
```

Weak:

```text
Dataset support is weak: retrieved examples were broad matches, so the draft is mainly based on your notes and disclosed estimates.
```

None:

```text
No useful dataset examples were available; the draft was generated from your notes, defaults, and disclosed assumptions.
```

Keep wording short and non-technical in the UI.

### 4. Add operator/debug support details

Add safe metadata for operator review, but do not expose raw prompts or raw provider responses.

Suggested fields:

- `support_level`;
- `support_reason`;
- `citation_support_count`;
- `weak_citation_count`;
- `strong_citation_count` if determinable;
- `support_message`;
- `should_claim_rag_grounded` boolean;
- `should_show_weak_support_warning` boolean.

Do not expose private paths, secret values, raw prompts, or large normalized internals.

### 5. Integrate into importer API response

Extend `RecipeImportResponse` / retrieval metadata safely so importer responses include the support policy result.

The API should make it clear whether the recipe is:

- strongly RAG-supported;
- partially RAG-supported;
- weakly supported;
- generated without useful retrieved examples.

Do not break existing response consumers or existing tests. If schema changes are needed, update tests and mock provider paths accordingly.

### 6. Update demo UI

Update the importer UI to show the support level/message near citations and retrieval metadata.

Example UI display:

```text
RAG support: Strong
Dataset examples closely matched this dish.
```

or:

```text
RAG support: Weak
Examples were broad matches; this draft is mainly based on your notes and estimated quantities.
```

The UI should not imply that citations are authoritative when support is weak.

### 7. Update citation display policy

When support is weak or moderate:

- show citations, but label them as broad/partial examples if appropriate;
- do not call them authoritative sources;
- do not say the recipe was fully grounded in them;
- keep provenance visible;
- preserve license/creator info.

When support is none:

- show a clear no-useful-citations message;
- still allow generation if user input is adequate;
- ensure generated assumptions are disclosed.

### 8. Update provider prompt guidance

Update importer prompt construction if needed so the model receives the support classification or weak-context instruction.

Rules:

- strong/moderate examples can inform structure, proportions, and step completeness;
- weak examples are structure-only and must not override user intent;
- if no examples are available, model should proceed from user notes and defaults only;
- user-provided requirements always control the recipe.

Do not include raw policy internals in the prompt.

### 9. Add tests

Add deterministic tests for:

- strong support classification;
- moderate support classification;
- weak support classification;
- no support classification;
- support message text is safe and concise;
- weak support does not set `should_claim_rag_grounded=true`;
- citations still display but are labeled honestly for moderate/weak support;
- API response includes support metadata;
- UI static tests cover support display;
- no raw prompts, raw provider responses, API keys, env values, or private paths appear in support metadata or UI strings.

### 10. Extend eval harness if useful

If practical, extend the retrieval eval harness so each retrieval case can assert expected support level.

Examples:

- baked cheesecake fixture with cheesecake matches -> strong;
- carbonara fixture with carbonara matches -> strong;
- omelet fixture with only breakfast-adjacent matches -> moderate or weak;
- distractor-only cheesecake fixture -> weak;
- no-match case -> none.

Normal evals must remain offline and deterministic.

### 11. Update docs

Update as needed:

- `docs/ai-evals-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/manual-recipe-entry-acceptance-2026-07.md` if present;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md` if relevant.

Create:

```text
outbox/0029B-9-rag-honesty-and-citation-support-policy-results.md
```

## Acceptance Criteria

- A deterministic RAG support policy exists.
- Support levels are limited to a small explicit taxonomy.
- Importer API responses include safe support metadata.
- Demo UI shows RAG support level/message.
- Weak/moderate citations are labeled honestly.
- The app no longer overstates weak RAG support as strong grounding.
- Tests cover strong/moderate/weak/none support cases.
- Existing retrieval, context packing, normalization, and mock paths still pass.
- Normal validation remains offline and mock-only.
- No live OpenAI calls are required.
- No raw dataset files or generated live artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke and live eval wrappers should skip cleanly unless explicit opt-in settings are present.

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI during normal validation.

## Optional Manual Validation Guidance

After completion, optional manual live validation can use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

Manual prompts:

```text
classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight

omelette for 4 with eggs cheddar onions butter folded in a skillet

make a dessert with sugar and cream

chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly
```

Expected signs:

- strong dish-specific matches show strong or moderate support;
- broad/generic prompts show weak or none;
- UI support message is visible;
- citations remain visible when present;
- weak citations are not described as authoritative grounding;
- generated assumptions remain disclosed;
- no raw prompt text or private paths appear in the UI.

## Non-Goals

- No embeddings
- No vector database
- No Qdrant
- No Postgres
- No pgvector
- No persistent generated index
- No production storage
- No production auth
- No paid access
- No public route exposure
- No Cloudflare changes
- No upstream Vanilla Cookbook frontend rewrite
- No browser automation
- No screenshots
- No raw dataset commits
- No large food ontology
- No ML reranker
- No long-term memory

## Commit

```bash
git add ai-api evals docs README.md outbox/0029B-9-rag-honesty-and-citation-support-policy-results.md

git commit -m "mailbox: complete task 0029B-9 rag honesty citation support policy"

git push origin main
```
