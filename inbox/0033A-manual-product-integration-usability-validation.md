# 0033A Manual Product Integration Usability Validation

## Goal

Manually validate the current local integration between the AI sidecar and the Vanilla Cookbook app as a production-usability exercise.

This is the next main effort after `0032A`. The purpose is to understand how the integrated product feels end to end and identify concrete usability/integration gaps before building additional product features.

## Context

AWS infrastructure work is now treated as a separate future portfolio-platform repository/effort. This Cookbook repo should refocus on app-level product validation and usability.

Current validated baseline includes:

- local product shell at `/product`;
- Vanilla Cookbook link/redirect through `/product/cookbook`;
- AI workspace through `/product/ai` / `/demo`;
- mock/offline validation for normal tests;
- explicit live importer manual acceptance for `openai` / `gpt-5.4-nano` at the 500-token diagnostic profile;
- plugin/adapter ADR for future seamless integration;
- QMD research spike as optional future retrieval candidate.

## Required Work

### 1. Read current integration and status docs

Read:

```text
docs/product-priority-roadmap-after-0032A.md
docs/local-cookbook-ai-product-integration.md
docs/ai-ui-integration-plan.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
docs/playwright-ui-troubleshooting.md
docs/cookbook-ai-plugin-adapter-architecture-adr.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

### 2. Create a manual validation plan

Create:

```text
docs/manual-product-integration-usability-validation.md
```

The plan should cover:

- local startup sequence;
- Docker Compose/Vanilla Cookbook expectations;
- AI sidecar startup expectations;
- product shell route checks;
- `/product`, `/product/cookbook`, `/product/ai`, and `/demo` flow;
- readiness panel expectations;
- mock mode behavior;
- live mode availability behavior without making live calls by default;
- manual importer acceptance boundary;
- Ask My Cookbook flow;
- Dataset Ask flow;
- Meal Planner flow;
- Recipe Session flow;
- UI consistency and seamlessness observations;
- errors, empty states, loading states, and navigation observations;
- what should feel production-ready vs what still feels like a local/demo shell;
- gap capture format;
- follow-up task candidates.

### 3. Perform mock/manual validation where safe

Run local validation in mock/offline mode by default. Do not run live OpenAI unless explicitly approved and documented as a separate manual step.

Use existing scripts where appropriate:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

In a second terminal, run safe checks such as:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

Manual browser checks should focus on product usability, not screenshots or browser artifacts. Do not commit screenshots, traces, recordings, or local artifacts.

### 4. Capture production-usability gaps

Create a structured gap list in the plan or a companion note. Include fields such as:

```text
Gap ID
Area
Observed behavior
Expected production behavior
Severity
Suggested follow-up task
Boundary/non-goal
```

Prioritize gaps that block the app feeling like one product instead of two linked demos.

### 5. Update docs/status

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

### 6. Add outbox report

Create:

```text
outbox/0033A-manual-product-integration-usability-validation-results.md
```

Summarize:

- validation plan created;
- manual/mock checks performed;
- product integration observations;
- top usability gaps;
- recommended follow-up tasks;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Manual product integration validation plan exists.
- Validation focuses on the AI sidecar + Vanilla Cookbook integration experience.
- Product-shell and AI-workspace flows are covered.
- Seamless UI/product expectations are evaluated.
- Gaps are captured in a structured format.
- Follow-up tasks are recommended but not implemented.
- Normal validation remains mock/offline.
- No live OpenAI call is made unless explicitly approved and documented.
- No AWS/platform/IaC work is added.
- No production auth, SSO, BYOS, analytics, ads, or monetization work is implemented.
- No screenshots, traces, browser artifacts, secrets, prompts, provider outputs, raw datasets, generated indexes, or local env values are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

If full browser/manual validation cannot be completed, record the limitation honestly in the outbox.

## Non-Goals

- no AWS resources;
- no Terraform/CDK/CloudFormation;
- no production deployment;
- no SSO implementation;
- no BYOS implementation;
- no analytics implementation;
- no ads/monetization implementation;
- no provider routing change;
- no live OpenAI during normal validation;
- no upstream UI rewrite;
- no screenshots or browser artifacts committed.

## Commit

```bash
git add docs README.md outbox/0033A-manual-product-integration-usability-validation-results.md

git commit -m "docs: add manual product integration validation"

git pull --rebase origin main

git push origin main
```
