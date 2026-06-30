# Task 0015 Results: Design AI Cookbook Medium Path

## Summary

Created a documentation-only design package for the 2-4 week AI portfolio expansion. The design keeps Vanilla Cookbook as a black-box container and adds a Python/FastAPI sidecar for recipe search, RAG assistant behavior, structured recipe import, meal planning, and offline evals.

No AI service code was implemented.

## Files Created

- `docs/ai-medium-path-roadmap.md`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `outbox/0015-design-ai-cookbook-medium-path-results.md`

## Files Modified

- `README.md`
- `docs/repo-map.md`
- `docs/architecture.md`

## Repo Inspection Findings

Inspection was run from the Windows clone at `/c/Users/scott/cookbook-roadmaps-link`. The task asks to stay in `/home/coder/repo`; this session is attached to the Windows checkout, while `/home/coder/repo` remains the documented Coder workspace path.

Key findings:

- Working tree was clean before changes: `## main...origin/main`.
- Latest commit before work: `c9d99ef mailbox: add task 0015 design ai cookbook medium path`.
- Existing Compose services are `app` and `cloudflared`.
- Existing app image is `jt196/vanilla-cookbook:stable`.
- Existing persistent data mounts are `./db:/app/prisma/db` and `./uploads:/app/uploads`.
- The app publishes `127.0.0.1:3000:3000`, not a public interface.
- The GitHub Actions workflow already references optional AI provider settings: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, and `OLLAMA_BASE_URL`.
- The workflow deploy path renders `.env` from GitHub Actions secrets/variables and sends it through SSM without printing it.
- Current docs cover architecture, runtime scaffold, EC2 control, Cloudflare, backup/restore, validation, operations, and mailbox continuation.

## Design Coverage

- `docs/ai-medium-path-roadmap.md` defines phases 0-6 with acceptance criteria.
- `docs/ai-sidecar-architecture.md` documents the sidecar design, Mermaid diagram, endpoint proposal, provider abstraction, secrets/config, exposure model, and risks.
- `docs/ai-evals-plan.md` documents unit tests, integration tests, golden fixtures, RAG checks, meal-plan checks, proposed directories, and example eval cases.
- `docs/ai-implementation-backlog.md` proposes follow-on mailbox tasks 0016-0024 with goals, likely files, validation, and done criteria.
- Existing docs now link to the AI docs from the README, repo map, and architecture document.

## Validation Commands Run

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Results:

- `bash -n scripts/validate-repo.sh`: passed through local Git Bash.
- `bash scripts/validate-repo.sh`: passed through local Git Bash.
  - Shell script syntax: PASS
  - Docker Compose configuration: PASS
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings.

## Assumptions

- The first AI implementation should not require local LLM inference on EC2.
- The Vanilla Cookbook SQLite schema must be inspected safely before reader code is written.
- The sidecar should start with read-only DB access and no direct write-back.
- Live provider calls should stay out of CI until cost, rate limits, and credentials are explicitly documented.
- Future AI API exposure should continue using Cloudflare Tunnel rather than opening EC2 inbound web ports.

## Risks And Unknowns

- The cookbook DB schema is not documented in this repo yet.
- Read-only SQLite access must avoid interfering with app writes.
- Search and RAG quality depends on how recipe ingredients and instructions are stored.
- Hosted AI providers introduce latency, cost, and outage risk.
- t3.micro capacity may limit indexing or local-model experiments.
- Importer write-back is intentionally deferred because direct DB writes need review and rollback planning.

## Recommended Next Task

Proceed with `0016: scaffold AI FastAPI sidecar`, keeping it minimal: health endpoint, config detection, Dockerfile, Compose wiring, and tests with no live provider calls.
