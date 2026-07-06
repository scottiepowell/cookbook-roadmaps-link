# Task 0026B: Add AI Portfolio README Polish

## Goal

Polish the AI cookbook feature set into a portfolio-ready README and supporting showcase docs.

`0026A` added the demo walkthrough, demo scripts, REST examples, and feature status matrix. This task should make the project easy for a recruiter, interviewer, customer, or freelance prospect to understand in 2 to 5 minutes from the repository landing page.

Focus on presentation, clarity, proof points, and safe screenshot/demo guidance. Do not add production infrastructure.

## Build On

Completed work:

- `0025C`: manual live OpenAI smoke tests
- `0025D`: OpenAI strict structured-output schema compatibility
- `0025E`: Windows-safe live smoke cleanup and recorded live validation
- `0026A`: AI demo walkthrough, demo scripts, request examples, and feature status matrix

Before implementing, confirm the repo has:

- `README.md`
- `docs/ai-demo-walkthrough.md`
- `docs/ai-feature-status.md`
- `scripts/demo-ai-mock.ps1`
- `scripts/demo-ai-live-smoke.ps1`
- `scripts/demo-ai-requests.http`
- `docs/live-openai-smoke-tests.md`
- `outbox/0026A-add-ai-demo-walkthrough-and-scripts-results.md`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

Improve portfolio presentation only.

Add or update docs so the repository clearly communicates:

1. What the AI sidecar does.
2. Why the architecture is credible.
3. What AI workflows are complete.
4. How grounding/citations are handled.
5. How offline evals and live smoke validation prove quality.
6. How to run the mock demo.
7. How to run the optional live OpenAI smoke demo safely.
8. What is intentionally not implemented yet.
9. What screenshots or demo captures would be useful later.

## Suggested Files

Create or modify as appropriate:

```text
README.md
docs/ai-portfolio-showcase.md
docs/ai-screenshot-capture-guide.md
docs/ai-feature-status.md
docs/ai-demo-walkthrough.md
docs/ai-implementation-backlog.md
docs/repo-map.md
outbox/0026B-add-ai-portfolio-readme-polish-results.md
```

Do not add actual screenshots unless they can be generated safely from mock/demo data with no secrets, no private recipe data, no private paths, and no provider keys. If screenshots are not generated in this task, add a clear capture guide and checklist instead.

## README Requirements

Update the repository README so a reader immediately sees the AI portfolio value.

Add a concise AI showcase section near the top with:

- one-paragraph overview;
- architecture summary: Vanilla Cookbook plus FastAPI AI sidecar;
- completed feature bullets;
- validation proof bullets;
- live OpenAI smoke proof using the recorded result;
- links to demo walkthrough, feature status, request examples, eval plan, and live smoke docs;
- clear note that normal validation is mock/offline and safe;
- clear note that no provider keys, raw datasets, generated indexes, or private env files are committed.

Keep it readable. Do not bury the project in too much detail.

## Portfolio Showcase Doc

Create `docs/ai-portfolio-showcase.md`.

Include:

- executive summary;
- architecture diagram in text/mermaid if safe and supported by existing docs style;
- feature list;
- validation evidence;
- sample demo commands;
- recorded live OpenAI validation block;
- interview talk track;
- freelance/customer positioning;
- future roadmap boundaries.

Suggested positioning language:

```text
This project demonstrates an offline-first AI application architecture with a FastAPI sidecar, deterministic retrieval, grounded provider prompts, citations/provenance, offline evals, and manual live provider validation.
```

Do not overclaim production readiness.

## Screenshot Capture Guide

Create `docs/ai-screenshot-capture-guide.md`.

Include a checklist for future screenshots, such as:

- README AI showcase section;
- AI feature status matrix;
- mock demo script passing;
- offline eval output;
- live smoke output with no secret values;
- REST client request/response examples;
- app homepage if available;
- OpenAI usage dashboard only if it contains no private billing/key details and is manually redacted.

Include safety rules:

- never show API keys or key prefixes;
- never show `.env` contents;
- never show Cloudflare token values;
- never show AWS account IDs/secrets unless redacted;
- never show private recipe/user data;
- prefer mock fixtures and generated demo data.

## Feature Status Tightening

Review `docs/ai-feature-status.md` and make sure the matrix is accurate and portfolio-readable.

Add a short "proof" column or section if useful:

- offline pytest;
- offline evals;
- live smoke;
- docs/examples.

Keep all claims grounded in actual completed tasks/outboxes.

## Backlog Update

Update `docs/ai-implementation-backlog.md`:

- mark `0026B` as complete after implementation;
- add a sensible next task recommendation.

Recommended next task after this one:

```text
0026C: Final AI Feature Completion Review
```

That future task should do an acceptance review and produce a final feature-completion matrix, but should not add new infrastructure.

## Non-Goals

Do not implement:

- production storage architecture
- deployment changes
- Cloudflare changes
- controller/demo launch workflows
- GitHub Actions live provider tests
- Qdrant
- Postgres
- pgvector
- embeddings
- vector database
- persistent generated indexes
- UI rewrites
- raw dataset commits
- generated artifact commits
- private environment file commits
- provider key commits

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
```

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

The live smoke wrapper should skip cleanly unless explicitly opted in. Do not run live OpenAI calls during normal validation.

## Outbox Report

Create:

```text
outbox/0026B-add-ai-portfolio-readme-polish-results.md
```

Include:

- Summary
- Files changed
- README changes
- Showcase docs added
- Screenshot/capture guidance added
- Validation results
- Whether actual screenshots were added or deferred
- Confirmation that normal validation stayed offline
- Confirmation that no private environment files, raw datasets, generated artifacts, or provider keys were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add README.md docs scripts outbox/0026B-add-ai-portfolio-readme-polish-results.md

git commit -m "mailbox: complete task 0026B add ai portfolio readme polish"

git push origin main
```

## Done Criteria

- README has a clear AI showcase section.
- Portfolio showcase doc exists.
- Screenshot capture guide exists or safe screenshots are added with no sensitive content.
- Feature status is accurate and portfolio-readable.
- Backlog is updated.
- Mock demo path still works.
- Live wrapper still skips safely by default.
- Normal validation passes or the known Windows direct-pytest issue is documented with Git Bash validator passing.
- No production infrastructure changes are made.
- No private environment files, raw datasets, generated artifacts, or provider keys are committed.
