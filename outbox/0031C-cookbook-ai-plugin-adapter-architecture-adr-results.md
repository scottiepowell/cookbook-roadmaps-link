# 0031C Cookbook AI plugin adapter architecture ADR results

Created [Cookbook AI Plugin and Adapter Architecture ADR](../docs/cookbook-ai-plugin-adapter-architecture-adr.md).

The ADR establishes the future direction:

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

It defines the plugin/adapter direction, core and sidecar ownership, plugin
manifest concept, Cookbook adapter contract, AI plugin API contract, auth/session
handoff concept, recipe read/write ownership, RAG/indexing boundary,
provider/mock/live boundary, UI integration levels, contract tests, security
requirements, and staged migration phases.

The ADR explicitly requires a seamless UX: consistent navigation and visual
language, natural AI actions, safe readable errors, accessible responsive
panels, and no visibly bolted-on split between the core Cookbook app and AI
sidecar. Operator/debug metadata remains separate from normal user views.

Docs were updated in `README.md`, `docs/ai-feature-status.md`, and
`docs/ai-implementation-backlog.md`.

Validation passed: `git diff --check`, the full repository validator (353
tests), existing offline evals (39/39), Docker Compose config, and mock/static
checks. No browser automation or live OpenAI call was run for this docs-only
task.

Explicit non-goals: no production integration, plugin or adapter endpoints,
production auth, public routes, AWS/platform/Cloudflare/DNS work, payment or
subscription work, new provider, vector database, embeddings, upstream UI
rewrite, live calls, browser automation, raw datasets/indexes, generated
artifacts, screenshots, traces, secrets, prompts, provider outputs, or local
environment values.
