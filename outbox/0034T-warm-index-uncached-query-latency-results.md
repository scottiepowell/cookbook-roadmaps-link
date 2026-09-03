# 0034T Warm-Index Uncached-Query Latency Results

Status: complete and deployed.

The deterministic scorer no longer renormalizes the same query anchors for
every document or linearly scans every field token for every query token.
Anchors are normalized once per query. The in-memory index stores exact token
sets and sorted token tuples, allowing the original bidirectional prefix
predicate to use set membership and binary search.

## Safe benchmark

With the 5,000-record real dataset and provider calls disabled:

- deployed 0034S warm uncached query: approximately 9.4 seconds;
- optimized 0034T warm uncached query: approximately 0.28 seconds;
- reduction: approximately 97 percent;
- optimized repeated retrieval-cache hit: approximately 0.05 seconds;
- result count and repeat ordering: unchanged and deterministic.

After deployment, the complete private mock-importer request path completed a
previously uncached query in approximately 0.50 seconds and its repeat in
approximately 0.06 seconds, with 3 retrieved examples, 2 packed examples, and
strong grounding. Sidecar readiness opened after approximately 77 seconds,
within the existing 120-second startup allowance.

The bounded cold index build remains protected by startup readiness. 0034T
does not prune candidates: all 5,000 documents still use the same scoring,
ordering, phrase, token-prefix, snippet, citation, relevance, and support rules.

## Result

- focused retrieval/RAG coverage passes with exact prefix-equivalence tests;
- no approximate search, persistent artifact, vector database, or embedding
  dependency was added;
- the public deployment uses core image
  `local/vanilla-cookbook-adapter:0034r` and sidecar image
  `local/cookbook-ai-sidecar:0034t`.

## Validation

- focused retrieval, normalization, cache, context, importer, and RAG tests:
  58 passed;
- full repository validation: 418 tests, 39 offline evals, and all 7 checks
  passed;
- production sidecar image build and Compose validation: passed;
- public health: HTTP 200;
- deployed core, sidecar, and tunnel: running, with sidecar healthy;
- dataset mount: present and read-only;
- sidecar host-published port: none;
- `git diff --check`: passed.

No raw dataset row, title, snippet, identifier, path, generated recipe, prompt,
provider response, secret, token, cookie, OAuth value, session value, or user
profile is recorded.
