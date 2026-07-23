# 0031D QMD local hybrid retrieval adapter spike results

Created [QMD Local Hybrid Retrieval Adapter Spike](../docs/qmd-local-hybrid-retrieval-adapter-spike.md).

QMD was inspected directly through its public GitHub repository and public
documentation. The spike records high-level runtime/package assumptions,
Markdown collections and search modes, CLI/MCP surfaces, local storage/index
artifacts, local model/runtime implications, and license/dependency
considerations. QMD was not installed or run.

The proposed direction keeps QMD optional and local-only behind a future
`RetrievalBackend` / `RetrievalAdapter` boundary. It includes a possible
generated Markdown snapshot strategy, Cookbook recipe-ID/title/snippet/citation
and provenance mapping, and a comparison against the current deterministic
keyword backend.

Potential benefits include semantic recall and hybrid ranking for paraphrased
recipe queries. Risks and unknowns include native runtime dependencies, model
downloads/cache size, resource use, semantic false positives, stale-index and
deletion handling, provenance mapping, process/HTTP boundaries, dependency and
model licensing, and maintenance cost.

The note preserves seamless UX: users must not see a QMD-specific screen,
backend switch, raw diagnostics, or changed recipe save/review semantics.

Updated `README.md`, `docs/ai-feature-status.md`, and
`docs/ai-implementation-backlog.md`.

Validation passed: `git diff --check` and the full repository validator (353
tests). No live OpenAI call, browser automation, QMD installation, model
download, snapshot/index generation, or production integration was performed.

Explicit non-goals: no QMD/Node/Bun/native dependency, GGUF model, vector or
embedding implementation, Docker service, plugin endpoint, UI rewrite,
production route/auth, AWS/platform/Cloudflare/DNS work, raw dataset or
generated artifact, screenshot, trace, secret, prompt, provider output, or
local environment value.
