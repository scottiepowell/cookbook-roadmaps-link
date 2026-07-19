# RAG Requirements Interaction Architecture

This is the entry document for the 0030A requirements-interaction design. The
full canonical design is [Recipe Session Requirements Architecture](recipe-session-requirements-architecture.md).

0030A is the product layer before and between importer generations. It is
separate from the completed 0029B retrieval hardening: 0029B makes a single
retrieval-and-generation request grounded, bounded, cited, and safe; 0030A
decides whether the user has supplied enough requirements to make that request
and whether a later message changes those requirements enough to retrieve
again.

## Decision flow

```text
user input -> input-quality gate -> extract requirements -> assess confidence
  -> one clarification when material information is missing
  -> retrieval and generation when ready
  -> classify later message -> reuse or refresh retrieval -> revise draft
```

The design rejects unusable input before retrieval or provider use. For usable
input, it asks no more than one bounded question in a turn. It generates when
the dish intent and material constraints are sufficiently clear, using safe,
disclosed assumptions for minor omissions.

## Clarification and refresh policy

Ask one bounded question when dish intent is unclear, ingredients conflict, a
method or food-safety detail materially changes the recipe, retrieval is too
weak because a user-specific detail is missing, or the input is too vague for
useful retrieval. Do not ask for minor details that can be safely disclosed as
assumptions, for an already usable request, or for chatter and formatting-only
messages.

Refresh RAG when a follow-up changes dish type, method, main ingredient,
dietary constraint, cuisine/style, equipment, time, or a serving change large
enough to change retrieval intent. Do not refresh for thanks, cosmetic wording,
formatting, irrelevant comments, or a regenerate request with unchanged
requirements. The safe response explains the decision, for example: “RAG was
refreshed because the cooking method changed from baked to no-bake.”

## Follow-up classification

The canonical design classifies a new message as a relevant requirement update,
clarification answer, correction to an assumption, irrelevant chatter,
formatting-only request, regenerate-without-new-requirements request, or
save/finalize request. Relevant updates are then evaluated against the refresh
policy; a classification alone never exposes raw prompts, provider responses,
paths, or secrets.

## Scope

The design is intentionally session-scoped and offline/mock-friendly. It does
not introduce production persistence, authentication, paid access, public
routes, database migrations, embeddings, vector databases, or a full chat UI.
For complete API examples, UI implications, multi-turn flows, and the offline
evaluation plan, see the [canonical architecture](recipe-session-requirements-architecture.md).
