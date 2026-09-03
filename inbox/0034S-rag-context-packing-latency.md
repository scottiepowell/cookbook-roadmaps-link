# 0034S - RAG Context-Packing Latency

## Goal

Reduce post-warmup importer retrieval/context-packing latency caused by
rebuilding a 5,000-record source map for every request.

## Required behavior

- measure the current provider-free real-dataset path using safe timings and
  aggregate retrieval outcomes only;
- reuse the existing warmed, fingerprinted deterministic index for context
  record lookup;
- preserve the 5,000-record limit, rankings, context bounds, citations,
  relevance/support policy, and cache invalidation behavior;
- keep the index in memory and create no dataset-derived artifact;
- add regression coverage proving a warm pack does not reread the dataset;
- build, deploy, validate, commit, and publish safe results.

## Non-goals

No provider/model change, vector database, embeddings, persistent index,
dataset API exposure, raw-row logging, core UI change, auth change, canonical
recipe write, Cloudflare/DNS change, or sidecar identity/session ownership.
