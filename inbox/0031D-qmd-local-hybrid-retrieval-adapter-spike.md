# 0031D QMD Local Hybrid Retrieval Adapter Spike

## Goal

Investigate whether QMD (`https://github.com/tobi/qmd`) should become an optional local hybrid-retrieval backend for the Cookbook AI sidecar.

QMD is being considered because it is described as an on-device search engine for markdown notes, meeting transcripts, documentation, and knowledge bases, combining BM25 full-text search, vector semantic search, and local LLM reranking via `node-llama-cpp` and GGUF models.

This is a design/research spike only. Do not add QMD as a runtime dependency in this task.

## Context

`0031C` established the future plugin/adapter architecture:

```text
cookbook.roadmaps.link core app
        |
        | stable app/plugin contract
        v
Cookbook AI Adapter
        |
        | stable AI sidecar API
        v
RAG/AI sidecar
```

QMD, if useful, should fit behind a retrieval adapter boundary. The core Cookbook app should not know QMD exists, and the user-facing UI should remain seamless.

Current sidecar retrieval is deterministic and mock/offline friendly. Embeddings/vector storage are still future work. QMD may be useful as an optional local backend for generated markdown snapshots of recipes, cookbook notes, project docs, transcripts, and other knowledge-base material.

## Required Work

### 1. Read current architecture docs

Read:

```text
docs/cookbook-ai-plugin-adapter-architecture-adr.md
docs/cookbook-ai-plugin-adapter-future-feature.md
docs/ai-sidecar-architecture.md
docs/local-cookbook-ai-product-integration.md
docs/ai-ui-integration-plan.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Use these as source of truth for the current sidecar, plugin/adapter boundary, mock/live behavior, and seamless UX requirement.

### 2. Inspect QMD only as an external candidate

If internet access is available, inspect the public QMD repository and summarize only high-level integration-relevant facts:

- runtime and packaging assumptions;
- query/index model;
- input document shape;
- storage/index artifacts;
- HTTP or CLI integration surface if present;
- local model/runtime implications;
- license and dependency considerations if easily available.

If internet access is not available, clearly state the limitation and base the spike only on the operator-provided description and local repo architecture.

Do not vendor QMD.
Do not install QMD.
Do not download models.
Do not generate indexes.
Do not add Node, GGUF, llama, sqlite-vec, or QMD dependencies to this repo.

### 3. Produce a spike note

Create:

```text
docs/qmd-local-hybrid-retrieval-adapter-spike.md
```

The note should cover:

- what problem QMD might solve;
- how QMD could fit behind a `RetrievalBackend` / `RetrievalAdapter` interface;
- possible markdown snapshot strategy for recipes and notes;
- how QMD results would map back to recipe IDs, titles, snippets, citations, and provenance;
- comparison against current deterministic keyword retrieval;
- likely benefits;
- risks and unknowns;
- local-only proof-of-concept shape;
- how to keep normal validation mock/offline;
- how to preserve seamless UI despite modular internals;
- security/data boundary requirements;
- explicit non-goals;
- go/no-go criteria for a later implementation task.

### 4. Define interface sketch

Include a design-only sketch such as:

```text
RetrievalBackend
  readiness() -> RetrievalReadiness
  search(query, filters, limit) -> RetrievalResults
  get_document(document_id) -> RetrievalDocument
  refresh_index(scope) -> RetrievalRefreshResult
```

and an optional backend shape:

```text
QmdRetrievalBackend
  - reads generated markdown snapshots only
  - keeps generated snapshots and indexes ignored/rebuildable
  - maps QMD hits back to Cookbook IDs/provenance
  - exposes no raw provider/model output to normal users
  - never writes directly to Cookbook DB
```

### 5. Update planning docs

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Keep the status clear: QMD is only a candidate for future optional local hybrid retrieval, not an accepted production dependency.

### 6. Add outbox report

Create:

```text
outbox/0031D-qmd-local-hybrid-retrieval-adapter-spike-results.md
```

Summarize:

- spike created;
- whether QMD was inspected directly or not;
- proposed adapter boundary;
- possible benefits;
- risks/unknowns;
- seamless UX implications;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- QMD spike note exists.
- The note treats QMD as optional/local-only unless future evidence supports adoption.
- The note keeps QMD behind a retrieval adapter boundary.
- The note preserves seamless end-user UX as a first-class requirement.
- The note defines markdown snapshot and provenance mapping concepts.
- The note compares QMD to current deterministic retrieval at a high level.
- The note defines risks, unknowns, and go/no-go criteria.
- No QMD dependency, Node runtime change, model download, generated index, raw dataset, or production route is added.
- No live OpenAI call is made.
- No secrets, prompts, provider outputs, screenshots, traces, generated artifacts, indexes, or local env values are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If full validation is too expensive for this design-only task, run the available doc/static checks and record the limitation honestly in the outbox.

## Non-Goals

- no QMD install;
- no QMD vendoring;
- no model download;
- no Node runtime or package-lock changes;
- no new service in Docker Compose;
- no generated markdown snapshots or indexes committed;
- no vector DB implementation;
- no embeddings implementation;
- no production integration;
- no plugin endpoint implementation;
- no UI rewrite;
- no AWS/platform/Cloudflare/DNS work;
- no live OpenAI calls;
- no provider changes.

## Commit

```bash
git add docs README.md outbox/0031D-qmd-local-hybrid-retrieval-adapter-spike-results.md

git commit -m "docs: add qmd retrieval adapter spike"

git pull --rebase origin main

git push origin main
```
