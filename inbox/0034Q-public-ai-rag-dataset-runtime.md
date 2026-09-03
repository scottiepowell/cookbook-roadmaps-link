# 0034Q — Public AI RAG Dataset Runtime

## Goal

Make the existing local recipe dataset and importer RAG examples available to
the deployed public AI sidecar so recipe drafts no longer fall back solely to
user notes because of a missing container path.

## Required behavior

- mount the existing ignored `recipe-dataset/` into the sidecar only;
- make the mount read-only and fail if the host dataset path is missing;
- configure the in-container dataset path explicitly;
- retain the bounded 5,000-record meaningful-RAG index profile;
- warm the in-memory index before public sidecar readiness so the first user
  request does not absorb the initial build time;
- do not mount the dataset into Cookbook core;
- do not expose a dataset route or sidecar port publicly;
- verify safe retrieval counts, relevance/support categories, and warning
  absence without recording raw dataset rows or generated provider output;
- rebuild, redeploy, validate, commit, and push the sidecar task.

## Non-goals

No dataset ingestion into the canonical Cookbook database, generated persistent
index, vector database, embeddings, image ingestion, user-recipe access,
automatic recipe save, Cloudflare/DNS change, or broader public route.
