# Task 0008: Create repository validation CI workflow

## Goal

Create a lightweight GitHub Actions validation workflow that checks repository quality before deployment-related work is used.

This task should add CI checks only. Do not run AWS, Cloudflare, OpenAI, or deployment commands. Do not commit secrets.

## Project context

The repo now has:

- Docker Compose runtime scaffold.
- Manual EC2 control and deployment workflow.
- EC2 bootstrap and preflight scripts.
- Cloudflare Tunnel/DNS runbook.
- Backup, restore, and operations scripts.
- README, architecture, first-deploy guide, and repo map.

Before first deployment, it would be useful to have a safe validation workflow that runs on push and pull request to catch common mistakes.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not run cloud-provider commands.
- Do not deploy anything.
- Do not require real GitHub Actions secrets for the validation workflow.
- Keep CI fast and Free Tier friendly.
- Prefer built-in shell checks and syntax validation over heavy tool installs.
- The validation workflow must not print `.env` content or secret-looking values.

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

### 2. Create `.github/workflows/repo-validation.yml`

Create a GitHub Actions workflow named:

```text
Repository Validation
```

It should run on:

- `push`
- `pull_request`
- `workflow_dispatch`

Use minimal permissions:

```yaml
permissions:
  contents: read
```

The workflow should checkout the repo and run safe validation steps.

### 3. Add validation coverage

The workflow should validate:

- Shell script syntax with `bash -n`.
- `deploy.sh` syntax.
- All shell scripts under `scripts/`.
- Docker Compose config using `.env.example` copied to a temporary `.env`.
- Markdown link/file sanity where practical without external services.
- Git whitespace with `git diff --check` or a comparable check.
- Secret-safety scan for common committed credential patterns.

The secret-safety scan should be conservative and avoid printing matched secret values. It can print filenames and rule names only. It should detect obvious patterns such as:

- AWS access key IDs.
- GitHub personal access token prefixes.
- OpenAI API key prefixes.
- Private key block headers.
- Cloudflare token-looking assignment names.

Do not fail on placeholder names in docs like `AWS_ROLE_ARN` or `CLOUDFLARE_TUNNEL_TOKEN` unless an actual token-like value is present.

### 4. Create `scripts/validate-repo.sh`

Create a local validation script that mirrors the CI checks as much as possible.

Requirements:

- Use `set -euo pipefail`.
- Run from the repo root or find the repo root.
- Validate shell syntax.
- Validate Docker Compose config using a temporary `.env` from `.env.example`.
- Run whitespace checks.
- Run a safe secret-pattern scan.
- Print a concise pass/fail summary.
- Do not print secret values.
- Clean up temporary files.

The GitHub Actions workflow should call this script.

### 5. Create `docs/repo-validation.md`

Document:

- What the validation workflow checks.
- How to run validation locally.
- What the secret-pattern scan is and is not.
- How to handle false positives.
- Why the workflow does not deploy or call cloud APIs.
- How this supports the GitOps mailbox workflow.

### 6. Update docs if useful

Add minimal links to the validation doc in:

- `README.md`
- `docs/repo-map.md`
- `docs/first-deploy-guide.md`

Only update files where the link is genuinely useful.

### 7. Validate locally

Run:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
```

Also run:

```bash
git diff --check
```

If `actionlint` is available, run it on workflows. If not available, do not install it just for this task. Mention availability in the outbox report.

Do not run AWS, Cloudflare, OpenAI, or deployment commands.

### 8. Create outbox report

Create:

```text
outbox/0008-create-repo-validation-ci-workflow-results.md
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
git add .github/workflows/repo-validation.yml scripts/validate-repo.sh docs/repo-validation.md README.md docs/repo-map.md docs/first-deploy-guide.md outbox/0008-create-repo-validation-ci-workflow-results.md
git commit -m "mailbox: complete task 0008 repo validation ci workflow"
```

If some documentation files are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `.github/workflows/repo-validation.yml` exists.
- `scripts/validate-repo.sh` exists and runs locally.
- `docs/repo-validation.md` exists.
- The workflow uses minimal permissions and does not require secrets.
- Validation checks shell syntax, Compose config, whitespace, and obvious committed secret patterns.
- Related docs link to validation where useful.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
