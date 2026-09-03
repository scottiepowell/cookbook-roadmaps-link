# 0034R Public AI RAG Provenance UX Results

Status: complete and deployed.

The authenticated public AI importer now shows a local-recipe grounding panel
below each successful draft. The core owns the disclosure boundary and emits
only a grounding boolean, counts capped at ten, allowlisted strong/moderate/
weak/none labels, and at most three deduplicated titles capped at 120
characters.

## Result

- the public UI distinguishes strongly grounded drafts from drafts where local
  examples were only reviewed;
- visible counts report examples found and examples used;
- relevance and support appear only when the sidecar value is allowlisted;
- up to three example titles are displayed after deduplication;
- tests prove retrieval queries, record/source IDs, snippets, paths, and
  internal labels do not cross the core response boundary;
- the existing authenticated proxy, `gpt-5.4-nano` pin, one bounded transient
  retry, rate/payload limits, private sidecar, and read-only dataset runtime are
  unchanged;
- the public deployment uses core image
  `local/vanilla-cookbook-adapter:0034r` and sidecar image
  `local/cookbook-ai-sidecar:0034q`.

## Validation

- core proxy tests: 6 passed;
- Svelte diagnostics: 0 errors and 0 warnings;
- production core image build: passed;
- sidecar repository validation: 415 tests, 39 offline evals, and all 7
  repository checks passed;
- Compose configuration: passed;
- public health: HTTP 200;
- anonymous `/ai`: HTTP 303 to the existing login boundary;
- deployed core/sidecar/tunnel containers: running, with the sidecar healthy;
- dataset mount: present and read-only;
- sidecar host-published port: none;
- `git diff --check`: passed in both repositories.

No raw dataset row, snippet, identifier, path, prompt, provider response,
secret, token, cookie, OAuth value, session value, or user profile is recorded.
