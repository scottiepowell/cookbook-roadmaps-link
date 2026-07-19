# Recipe Creator Session Memory Model

This companion document makes the session-memory portion of the 0030A design
easy to locate. Its normative source is [Recipe Session Requirements
Architecture](recipe-session-requirements-architecture.md).

## Boundary

Memory is short-lived, interaction-scoped state for a single recipe-creation
flow. It supports clarification, revisions, retrieval reuse, and safe UI
explanations. It is not long-term user memory, production storage, a database
schema, a persistent cache, or a record of raw prompts/provider responses.

## Requirements state

Each interaction holds an opaque `interaction_id`, original and latest user
text, interpreted dish intent, serving count, required/optional/excluded
ingredients, method, equipment, time, dietary, and texture/style constraints.
Every interpreted requirement records a source: `user-provided`, `inferred`,
`defaulted`, `RAG-supported`, or `clarified-by-user`.

It also holds a confidence label, assumptions, at most the currently open
clarification question, resolved questions, revision count, and bounded
timestamps (`created_at`, `updated_at`, `expires_at`). Safe serialized state
omits provider prompts and responses, API/environment values, local paths,
logs, and secrets.

## Retrieval snapshot

The state retains only the information needed to explain and reuse the most
recent retrieval:

- normalized retrieval query and safe retrieval-cache key;
- anchors used and matched result IDs;
- citation summaries/IDs and support quality label;
- created and expiry times;
- revision number; and
- a reason retrieval was refreshed or deliberately reused.

For a materially changed requirement, a new snapshot can retain previous
citation IDs for a user-facing comparison without persisting raw dataset
content. Equivalent retrieval uses the existing process-local cache where
available; interaction memory does not create a disk cache or persistent index.

## Lifecycle

1. Start: extract requirements, assess confidence, and either retain an open
   question or attach the first retrieval snapshot.
2. Follow-up: classify the message and merge only relevant requirement deltas.
3. Refresh: replace the current retrieval snapshot when a material constraint
   changes; otherwise record the no-refresh reason and preserve the snapshot.
4. Finalize/expire: expose a safe draft-ready state only; do not write to a
   cookbook database. Discard the bounded interaction state on expiry.

The canonical architecture specifies the proposed start/message/get/finalize
API states, UI presentation, safety cases, and offline evaluation coverage.
