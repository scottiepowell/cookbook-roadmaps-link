# 0030I-8T bounded live importer schema completion tuning results

The baseline diagnostic reached the live provider path with valid
`openai/gpt-5.4-nano` configuration but returned the safe category
`output_cap_or_incomplete_response` and `JSONDecodeError`.

The bounded diagnostic now uses a deterministic scrambled-egg fixture and the
accepted 300-token cap, while the full-RAG importer evaluation retains its
separate larger manual profile. The provider remains strict schema JSON and
invalid or incomplete JSON is never accepted as success. Safe parser/category
mapping and no-retry behavior remain intact.

Tests cover the minimal fixture, approved model/cap, fake successful summaries,
incomplete output classification, safe error output, and no secret/provider
body leakage. No live provider call was made for this task.

Validation passed: env-loader, 350-test Git Bash validator, 39 offline evals,
mock smoke, Docker config, and Playwright mock UI 4/4. Live wrappers skipped.

Explicit non-goals: no live success claim, retries, arbitrary models, cap
changes to normal validation, raw provider output, secrets, AWS/platform work,
production storage/auth, public exposure, screenshots, browser artifacts,
vector DB, embeddings, raw datasets, persistent indexes, or disk cache.

A successful live importer acceptance cannot be claimed until one explicitly
approved operator run completes and records only safe provider/model/status
facts; no such run was performed here.
