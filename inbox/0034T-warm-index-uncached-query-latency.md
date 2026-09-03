# 0034T - Warm-Index Uncached-Query Retrieval Latency

## Goal

Reduce the first-query scoring latency after the bounded recipe index is warm,
without changing deterministic search results or the RAG support policy.

## Required behavior

- profile the provider-free scorer using only safe timing/count outcomes;
- eliminate repeated per-document normalization and linear token-prefix scans;
- preserve the exact whole-phrase and bidirectional token-prefix predicates;
- continue scoring all bounded documents without approximate candidate pruning;
- preserve deterministic ordering, scores, snippets, citations, relevance,
  support, cache invalidation, and the 5,000-record limit;
- keep all indexes in memory with no dataset-derived artifact;
- add focused equivalence/regression coverage;
- build, deploy, validate, commit, and publish safe results.

## Non-goals

No provider/model change, vector database, embeddings, approximate retrieval,
persistent index, dataset API exposure, raw-row logging, UI/auth change,
canonical write, Cloudflare/DNS change, or sidecar identity/session ownership.
