# QMD Local Hybrid Retrieval Adapter Spike

Status: candidate investigation only, docs-only

Date: 2026-07-23

## Scope and conclusion

This spike investigates whether QMD could become an optional local hybrid
retrieval backend for the Cookbook AI sidecar. It does not install, vendor, or
run QMD, download models, generate snapshots or indexes, add dependencies, or
change runtime behavior.

The current conclusion is: keep QMD as an unaccepted, optional candidate behind
the retrieval adapter boundary. It may be worth a later isolated proof of
concept if it can demonstrate better retrieval quality or operator ergonomics
without compromising deterministic fallback behavior, provenance, data scope,
startup cost, or the seamless Cookbook UX. This task is not a go decision for a
production dependency.

## Current architecture constraint

The future integration architecture remains:

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

The core Cookbook app owns canonical recipes, users, authorization, storage,
and product UI. The adapter owns scoped translation and provenance mapping. The
sidecar owns retrieval orchestration, AI workflows, provider controls, and safe
responses. The core app and user-facing UI must not know that QMD exists.

Modular internals cannot create a visibly bolted-on product. If QMD is ever
used, AI actions, loading states, empty states, errors, citations, and recipe
review flows must remain coherent with the native Cookbook experience.

## External candidate facts inspected

The public [tobi/qmd repository](https://github.com/tobi/qmd) and its [QMD
documentation](https://tobi-qmd-3.mintlify.app/) were inspected at a high
level. The following are observations from those sources, not guarantees for a
future integration:

| Area | Candidate fact | Integration implication |
| --- | --- | --- |
| Runtime and packaging | QMD is presented as a Node/Bun CLI and library, published as `@tobilu/qmd`; its package metadata declares Node `>=22.0.0`. | It would introduce a runtime/toolchain boundary that does not match the current Python sidecar by default. Prefer an optional process or separately approved adapter rather than adding Node to this repo. |
| Query/index model | It exposes keyword BM25 search, vector search, and a hybrid query path with query expansion and LLM reranking. The docs describe Markdown-aware chunking and score fusion. | It could complement exact ingredient/title matching with semantic recall, but introduces embedding/reranking behavior that needs deterministic evaluation and resource budgets. |
| Input document shape | Collections point at directories with Markdown glob patterns; context can be attached to collection/path prefixes. Search can return structured JSON or file-oriented output. | Recipe snapshots could be Markdown documents with stable front matter and section headings, but snapshot schema and escaping need a future contract. |
| Storage and artifacts | QMD documents a local configuration file, a local SQLite index, collection paths, cache/model locations, and generated embeddings. | All snapshots, config, indexes, caches, and models would need to be ignored, scoped, rebuildable, and outside committed repository data. |
| CLI/HTTP surface | The candidate exposes CLI commands for collection setup, update, search, vector search, hybrid query, document retrieval, and status. It also documents MCP over stdio and optional localhost HTTP transport. | A future adapter could use a tightly scoped CLI subprocess or local transport, but neither should be treated as a production API without isolation, timeout, argument, output, and origin controls. |
| Local model/runtime implications | The repository lists `node-llama-cpp`, `better-sqlite3`, `sqlite-vec`, and related native/tree-sitter dependencies. The documentation describes local GGUF models, with models auto-downloaded on first use. | Installation size, native builds, CPU/GPU compatibility, model provenance, warm-up latency, and offline reproducibility are material unknowns. This repo must not add them in this spike. |
| License and dependency considerations | The GitHub repository displays an MIT license and a package dependency graph with native components. | MIT licensing alone does not resolve transitive license, security, maintenance, model-license, or operational review. Those require a later dependency gate. |

The public docs also describe `qmd://collection/path` references and short
document IDs. A future adapter could use those as internal lookup hints, but
Cookbook IDs and authorization remain authoritative; QMD paths or docids must
never become user-facing canonical identifiers.

## Problem QMD might solve

The current sidecar uses deterministic bounded keyword retrieval over local
recipe/dataset fixtures. That approach is attractive because it is simple,
offline, inspectable, cheap, and stable. It can nevertheless miss useful
matches when a user expresses a cooking concept with different wording, such
as a method, synonym, or contextual phrase that does not share exact tokens.

An optional hybrid backend might improve recall for:

- semantically similar cooking methods and ingredient descriptions;
- natural-language questions over recipe notes;
- long-form recipe content where exact keyword ranking is insufficient;
- bounded related-recipe discovery while retaining exact title/ingredient
  anchors and provenance.

QMD is not automatically a solution to recipe correctness. Semantic matches can
be plausible but wrong, and reranking can add latency or hide why a result was
selected. The candidate must therefore remain subordinate to anchor-aware
filters, source scope, citations, and deterministic safety rules.

## Retrieval adapter boundary

QMD, the current keyword implementation, or a future backend should fit behind
the same design-only interface:

```text
RetrievalBackend
  readiness() -> RetrievalReadiness
  search(query, filters, limit) -> RetrievalResults
  get_document(document_id) -> RetrievalDocument
  refresh_index(scope) -> RetrievalRefreshResult
```

Suggested safe concepts:

```text
RetrievalReadiness
  backend_name
  status: available | unavailable | stale | disabled
  capabilities
  source_scope
  last_refresh_safe_timestamp
  safe_reason

RetrievalResults
  items[]
    source_recipe_id
    title
    snippet
    score_summary
    match_kind: lexical | semantic | hybrid
    citation_id
    provenance
  support_level
  warnings

RetrievalDocument
  source_recipe_id
  source_version
  title
  bounded_sections
  citation_id
  provenance

RetrievalRefreshResult
  status
  scope
  indexed_count
  skipped_count
  removed_count
  safe_reason
```

The interface is a design seam, not an implementation request. It should be
owned by the sidecar/adapter layer and return product-safe view models. The
core app should receive recipe IDs, titles, snippets, citations, provenance,
and bounded status—not QMD-specific scores, file paths, SQL, docids, or raw
backend output.

### Optional QmdRetrievalBackend shape

```text
QmdRetrievalBackend
  - reads generated markdown snapshots only
  - keeps generated snapshots and indexes ignored/rebuildable
  - maps QMD hits back to Cookbook IDs/provenance
  - exposes no raw provider/model output to normal users
  - never writes directly to Cookbook DB
```

The backend should be optional and selected by sidecar configuration, not by a
browser flag. If it is unavailable, stale, over budget, or fails a contract
check, the sidecar should use the current deterministic backend or return a
safe unavailable state according to workflow policy.

## Possible Markdown snapshot strategy

For a later local-only proof of concept, the adapter could materialize a
generated Markdown snapshot per authorized recipe into an ignored temporary
directory. A conceptual document could look like:

```markdown
---
source_type: cookbook_recipe
source_recipe_id: <opaque-cookbook-id>
source_version: <stable-version>
title: <display-safe-title>
visibility_scope: <adapter-controlled-scope>
---

# <title>

## Ingredients

- <bounded ingredient line>

## Instructions

1. <bounded instruction line>
```

This is a shape sketch only; no snapshot should be generated by this task.

Requirements for any future snapshot writer:

- write only authorized, bounded fields supplied by the adapter;
- use stable opaque Cookbook recipe IDs and source versions in front matter;
- preserve display text safely while preventing front matter injection;
- omit private profile fields, credentials, raw provider content, and unrelated
  cookbook data;
- use deterministic content hashes to detect changes and deletions;
- write to a task-scoped ignored directory outside committed source data;
- make snapshots disposable and rebuildable from canonical Cookbook records;
- maintain an explicit mapping layer from backend document IDs to Cookbook IDs,
  never trusting a path alone;
- remove or tombstone snapshots when authorization or source records change.

QMD collections should never point at the canonical Cookbook database directory
or an unrestricted application data directory. The adapter, not QMD, decides
which recipe scope is exported.

## Result and provenance mapping

A future adapter would translate each backend hit as follows:

```text
QMD hit
  qmd://collection/path or qmd docid
  title / chunk text / score / match metadata
        |
        v
adapter mapping
  source_recipe_id + source_version lookup
  authorization and scope check
  bounded snippet extraction
  citation/provenance normalization
        |
        v
sidecar result
  recipe ID / title / snippet / citation ID / provenance / support level
```

The mapping must verify that the hit belongs to the current authorized scope
and source version. A missing mapping, stale version, or deleted recipe is a
non-result or safe warning, not an opportunity to display an unverified hit.
Scores are backend evidence only. The sidecar may combine them with exact
title/ingredient anchors and support policy; it must not present a semantic
match as authoritative recipe truth.

## Comparison with current deterministic retrieval

| Dimension | Current deterministic keyword retrieval | Optional QMD candidate |
| --- | --- | --- |
| Runtime | Existing Python sidecar path; no extra runtime | Node/Bun and native/local model assumptions need isolation. |
| Matching | Exact/normalized keywords, aliases, phrases, anchors | BM25 plus optional vector search and reranking. |
| Reproducibility | High and easy to fixture-test | Depends on model versions, index state, hardware, and reranker settings. |
| Explainability | Direct token/anchor evidence | Requires careful score/provenance translation; semantic relevance can be less obvious. |
| Startup/cost | Small bounded local cost | Model load, embedding, native dependency, cache, and refresh costs may be material. |
| Offline behavior | Existing normal validation baseline | Possible locally, but only after dependencies/models are provisioned separately. |
| Data handling | Reads current bounded local records | Requires generated Markdown snapshots and derived artifacts. |
| Fallback | Already available and known | Must remain the default-safe fallback if QMD is unavailable or stale. |
| Likely value | Strong exact dish/ingredient precision | Potential semantic recall for paraphrases and broader context. |

QMD should not replace anchor-aware deterministic retrieval until an isolated
evaluation shows a material improvement without unacceptable false positives,
latency, resource use, or provenance loss.

## Risks and unknowns

- Native Node, SQLite, vector extension, and model compatibility on supported
  operator machines is unverified.
- QMD's documented model downloads and cache footprint may conflict with
  offline, repeatable, or constrained local environments.
- Search and rerank quality for recipe-specific quantities, methods, allergens,
  and substitutions is unknown.
- Semantic similarity can outrank exact safety-critical constraints such as
  `no-bake`, excluded ingredients, or dietary boundaries.
- Index refresh and deletion behavior could expose stale or unauthorized data.
- Mapping QMD docids and paths back to canonical recipe IDs needs durable
  source-version metadata and failure tests.
- CLI/MCP/HTTP subprocess boundaries add timeout, process, port, output, and
  local-origin security concerns.
- A local reranker may add latency, memory, thermal, or GPU/CPU variability.
- Transitive dependency, native binary, model, and license reviews remain
  incomplete.
- QMD's project and interfaces may evolve faster than this application's
  adapter contract.
- A second retrieval backend can complicate support, fixtures, observability,
  and user-visible failure explanations.

## Local-only proof-of-concept shape

If a later task receives approval, the smallest useful proof of concept should:

1. Use a separate temporary workspace and a tiny synthetic Markdown fixture,
   not committed recipe data or the production database.
2. Keep the existing deterministic backend as the baseline and compare fixed
   query cases for exact anchors, paraphrases, no-bake constraints, excluded
   ingredients, and no-match behavior.
3. Run QMD outside the repository's runtime and dependency graph, using an
   operator-provisioned installation and models documented separately.
4. Exercise only a narrow adapter contract: readiness, search, document
   retrieval, and refresh status.
5. Verify hit-to-recipe mapping, source scopes, deletion/version behavior,
   bounded snippets, safe citations, timeout behavior, and fallback.
6. Record only aggregate metrics and safe statuses; do not commit snapshots,
   indexes, model files, raw results, prompts, or provider output.
7. Keep the proof of concept behind an explicit local configuration switch and
   ensure the default path remains deterministic keyword retrieval.

This task intentionally performs none of those installation, model, snapshot,
index, or runtime experiments.

## Keeping normal validation mock/offline

Normal validation must continue to use the current deterministic retrieval and
mock provider. Repository tests must not require QMD, Node, GGUF models,
network access, an index, or a running local QMD server. A future optional
backend may have a separate operator-only test profile, but the default test
suite must prove:

- QMD is not imported or invoked in the default path;
- unavailable/stale QMD falls back safely;
- strict recipe/session schemas remain unchanged;
- citations and provenance remain safe and source-grounded;
- no provider key, prompt, provider body, local path, or raw backend output is
  emitted;
- live OpenAI remains behind existing server-side opt-in and budget gates.

## Seamless UX despite modular internals

The UI should call core-app view models or adapter methods, not QMD commands.
Users should see the same navigation, typography, spacing, loading and empty
states, accessible controls, responsive layout, citations, and safe errors
whether the deterministic backend or QMD candidate supplied the result.
Backend choice, readiness detail, scores, and refresh diagnostics belong only
in appropriate operator/debug views. A backend switch must not create a second
search page, a separate login, a visible sidecar jump, or different recipe
save/review semantics.

## Security and data boundaries

- The core app remains the authority for authorization and canonical recipe
  truth.
- The adapter exports least-privilege, bounded Markdown snapshots only.
- QMD never writes directly to the Cookbook database.
- Snapshot and index paths are task-scoped, ignored, rebuildable, and never
  public routes or browser-readable storage.
- Backend identifiers map to canonical recipe IDs only after scope and version
  validation.
- No raw local paths, private environment values, credentials, prompts,
  provider responses, or model internals are returned to normal users.
- Any future local HTTP/MCP transport must bind narrowly, authenticate the
  caller where required, validate arguments, limit output, and avoid public
  exposure.
- Model files and derived indexes require separate provenance, license,
  retention, deletion, and malware/security review.
- Core app write-back remains explicit, authorized, reviewable, and transactional.

## Go/no-go criteria for a later implementation task

Do not implement a QMD backend until a separately approved task can show all of
the following with a synthetic, isolated fixture:

- measurable retrieval improvement over the deterministic baseline for agreed
  recipe queries, with no unacceptable regressions on exact anchors;
- no-bake, allergen, exclusion, quantity, and no-match cases remain safe;
- stable source-ID/version mapping produces correct titles, snippets, citations,
  and provenance, including deletion and stale-index cases;
- QMD can be disabled or unavailable without breaking the sidecar or UX;
- resource, startup, refresh, timeout, and memory budgets are acceptable;
- dependency, native-runtime, model-license, security, and maintenance reviews
  pass;
- snapshot/index isolation and cleanup are verified;
- the proposed CLI/MCP/HTTP boundary has an approved security design;
- normal mock/offline validation remains dependency-free and unchanged;
- the native Cookbook UI can present identical safe states and accessible
  interactions regardless of backend choice;
- no production route, auth, deployment, or provider change is required before
  a separate approval.

Until then, the current deterministic keyword backend remains the accepted
retrieval path and QMD remains a local-only candidate.

## Explicit non-goals

This spike does not:

- install or vendor QMD;
- add Node, Bun, GGUF, `node-llama-cpp`, `better-sqlite3`, `sqlite-vec`, or QMD
  dependencies to this repository;
- download models or generate Markdown snapshots, embeddings, indexes, caches,
  or other artifacts;
- implement vector databases, embeddings, a new service, Docker Compose changes,
  plugin endpoints, adapter endpoints, or production integration;
- change the current sidecar, provider, mock/live boundary, or strict schemas;
- rewrite the upstream Vanilla Cookbook UI or add browser automation;
- start AWS, platform, Cloudflare, DNS, auth, payment, or subscription work;
- make live OpenAI calls;
- commit raw datasets, generated Markdown, indexes, screenshots, traces,
  secrets, prompts, provider outputs, or local environment values.

## Sources

- [QMD GitHub repository](https://github.com/tobi/qmd) — repository README,
  package metadata, CLI/MCP usage, and MIT license.
- [QMD documentation](https://tobi-qmd-3.mintlify.app/) — search modes,
  collections, model/cache notes, document IDs, outputs, and local runtime
  descriptions.
- [Cookbook AI Plugin and Adapter Architecture ADR](cookbook-ai-plugin-adapter-architecture-adr.md)
  — local ownership and adapter boundary.
