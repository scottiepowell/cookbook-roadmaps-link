# Shared Infrastructure Data Boundaries

The portfolio platform may eventually share infrastructure across demos, but demo data planes should stay isolated.

Future shared components may include:

- controller state in Postgres;
- Qdrant as infrastructure for vector search;
- other reusable platform services.

Those components are not implemented now. This repository should not add Postgres, Qdrant, pgvector, embeddings, or a vector database until a later reviewed task explicitly scopes them.

If shared infrastructure is added later, individual apps should keep separate collections, indexes, schemas, credentials, and data lifecycle rules. Cookbook, stock market, and Army demos should not share one combined vector corpus. Cross-demo isolation matters for provenance, deletion, privacy, evaluation quality, and avoiding accidental retrieval across unrelated domains.
