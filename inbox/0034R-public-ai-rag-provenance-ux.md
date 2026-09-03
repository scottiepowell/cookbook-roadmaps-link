# 0034R - Public AI RAG Provenance UX

## Goal

Show authenticated public Cookbook users whether local recipe examples helped
ground an AI draft without exposing sidecar-private retrieval data.

## Required behavior

- reduce the importer response at the core boundary to safe, bounded fields;
- show a provenance panel below a successful AI draft;
- include a grounding boolean, bounded retrieved/used/citation counts,
  allowlisted relevance/support labels, and at most three citation titles;
- deduplicate and length-bound visible titles;
- keep retrieval queries, record/source IDs, snippets, scores, paths, packed
  context, prompts, provider output, and sidecar-only metadata private;
- retain the authenticated proxy, nano-model pin, rate/payload limits, one
  transient retry, private sidecar networking, and read-only dataset mount;
- build, deploy, validate, commit, and publish the task results.

## Non-goals

No dataset API exposure, raw-row display, canonical recipe write, saved-recipe
RAG, vector database, embedding pipeline, provider/model change, auth change,
Cloudflare/DNS change, or sidecar identity/session ownership.
