# 0034S RAG Context-Packing Latency Results

Status: complete and deployed.

The importer context packer now reuses a source-ID document lookup owned by
the same fingerprinted in-memory index used for retrieval. The lookup is built
once with the index and follows its existing TTL, file fingerprint, record
limit, and invalidation behavior.

## Safe benchmark

Using the deployed dataset limit and the same provider-free recipe query:

- prior warmed repeat: approximately 781 ms;
- optimized warmed repeat: approximately 94 ms;
- reduction: approximately 88 percent;
- output parity: 3 examples retrieved, 2 packed, strong grounding;
- one-time cold index construction: approximately 59 seconds before and after,
  still covered by startup warmup/readiness.

After deployment, the long-lived sidecar completed a repeated warmed query in
approximately 78 ms with the same 3/2/strong outcome. Its first previously
uncached query took approximately 9.4 seconds, isolating index scoring as a
separate follow-up rather than context-map reconstruction. That follow-up is
queued as 0034T and is not implemented by this task.

## Result

- repeated context packing no longer reparses or remaps all 5,000 records;
- regression coverage fails if a warm pack attempts another dataset read;
- deterministic ordering, context character/example bounds, citations,
  relevance labels, support policy, and provenance UX are unchanged;
- no persistent index or dataset-derived file is created;
- the public deployment uses core image
  `local/vanilla-cookbook-adapter:0034r` and sidecar image
  `local/cookbook-ai-sidecar:0034s`.

## Validation

- focused retrieval, importer, context, and RAG tests: 42 passed;
- full repository validation: 416 tests, 39 offline evals, and all 7 checks
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
