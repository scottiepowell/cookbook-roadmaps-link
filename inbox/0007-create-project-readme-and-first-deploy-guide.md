# Task 0007: Create project README and first-deploy guide

## Goal

Create a clear top-level project README, a first-deploy guide, and a lightweight architecture diagram so the repo is easy to understand and execute from start to finish.

This task should create documentation and safe validation only. Do not create cloud resources, do not run AWS or Cloudflare commands, and do not commit secrets.

## Project context

This repo is a GitOps mailbox-driven DevOps lab for deploying Vanilla Cookbook at:

```text
https://cookbook.roadmap.links
```

Current project pieces:

- Task 0002 created Docker Compose runtime files.
- Task 0003 created the GitHub Actions EC2 control and SSM deployment workflow.
- Task 0004 created EC2 bootstrap and preflight assets.
- Task 0005 created Cloudflare Tunnel/DNS runbook and verification scripts.
- Task 0006 created backup, restore, and day-2 operations runbooks.

The project now needs a clean entry point and a first-deploy sequence that ties everything together.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not include real AWS account IDs, Cloudflare tokens, OpenAI API keys, GitHub tokens, or domain-control values.
- Do not run AWS, Cloudflare, or OpenAI commands.
- Keep documentation practical and copy-paste friendly.
- Keep the README concise but complete.
- Link to existing docs instead of duplicating every detail.

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
find . -maxdepth 4 -type f | sort
```

Record key findings in the outbox report.

### 2. Create or update top-level `README.md`

Create a polished project README that includes:

- Project name.
- Short description.
- Architecture summary.
- What the app is: Vanilla Cookbook.
- Public target URL: `https://cookbook.roadmap.links`.
- Main technologies:
  - Coder
  - Codex
  - GitHub
  - GitHub Actions
  - AWS EC2
  - AWS Systems Manager
  - Docker Compose
  - Cloudflare Tunnel
- Security model:
  - no app inbound HTTP/HTTPS on EC2
  - Cloudflare Tunnel publishes the app
  - GitHub Actions secrets hold sensitive values
  - AWS OIDC avoids static AWS keys
- Quick-start path using existing docs.
- Link list to important docs.
- GitOps mailbox workflow explanation.
- Current status and what still needs to be configured manually.

Keep it readable and useful for a reviewer or interviewer.

### 3. Create `docs/architecture.md`

Create an architecture document that includes:

- A simple text diagram.
- Component descriptions.
- Runtime flow.
- Deployment flow.
- Secrets flow.
- Backup/restore flow.
- What is intentionally not exposed.

Use Mermaid if useful, but also include a plain-text diagram so it remains readable everywhere.

Do not include live secrets or account-specific values.

### 4. Create `docs/first-deploy-guide.md`

Create a first-deploy guide that gives the exact order of operations.

Include these phases:

1. Confirm repo and local Coder workspace are ready.
2. Prepare AWS EC2 host.
3. Configure AWS IAM OIDC and instance profile.
4. Configure GitHub Actions secrets and variables.
5. Configure Cloudflare Tunnel and public hostname.
6. Run GitHub Actions workflow in this order:
   - `status`
   - `start`
   - `deploy` with `stop_after_deploy=false`
7. Run local EC2 verification.
8. Run public Cloudflare route verification.
9. Open the app and create or verify the first admin user.
10. Create the first backup.
11. Stop EC2 when done.

Include links to the relevant existing docs for each phase.

### 5. Create `docs/repo-map.md`

Create a small repo map that explains the purpose of the main files and folders:

- `.github/workflows/`
- `docs/`
- `inbox/`
- `outbox/`
- `scripts/`
- `.env.example`
- `docker-compose.yml`
- `deploy.sh`

### 6. Update related docs if useful

Add minimal links to the new README or first-deploy guide in existing docs if useful:

- `docs/github-settings-checklist.md`
- `docs/operations-runbook.md`
- `docs/runtime-scaffold.md`

Only update files where the link is genuinely useful.

### 7. Validate as much as possible

Run:

```bash
git diff --check
bash -n deploy.sh
find scripts -maxdepth 1 -name '*.sh' -print -exec bash -n {} \;
```

If markdownlint is available, run it on Markdown files. If it is not available, do not install it just for this task. Mention availability in the outbox report.

Do not run AWS, Cloudflare, or OpenAI commands.

### 8. Create outbox report

Create:

```text
outbox/0007-create-project-readme-and-first-deploy-guide-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 9. Commit changes

If possible, commit with:

```bash
git add README.md docs/architecture.md docs/first-deploy-guide.md docs/repo-map.md docs/github-settings-checklist.md docs/operations-runbook.md docs/runtime-scaffold.md outbox/0007-create-project-readme-and-first-deploy-guide-results.md
git commit -m "mailbox: complete task 0007 project readme and first deploy guide"
```

If some documentation files are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `README.md` exists and is useful as the project entry point.
- `docs/architecture.md` exists.
- `docs/first-deploy-guide.md` exists.
- `docs/repo-map.md` exists.
- Related docs link to the new first-deploy guide where useful.
- Validation has been performed.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
