# Task 0010: Create local resume and first-deploy readiness guide

## Goal

Create a practical recovery/resume guide for continuing this project after re-cloning the repository on Windows and restarting the Coder/Codex workflow.

This task should update documentation and create a readiness checklist only. Do not create cloud resources, do not run AWS or Cloudflare commands, and do not commit secrets.

## Project context

The operator re-cloned the repository on Windows at:

```text
C:\Users\scott\cookbook-roadmaps-link
```

Current known project state:

- GitHub repo: `scottiepowell/cookbook-roadmaps-link`
- Current public hostname: `cookbook.roadmaps.link`
- EC2 instance created: `i-0bdd490b3a71ccddd`
- AWS region: `us-east-2`
- GitHub variables/secrets have been updated by the operator.
- Cloudflare Tunnel secret has been saved by the operator.
- The next operational steps are to restore the local/Coder workflow, bootstrap/preflight EC2 through Systems Manager, and then run the GitHub Actions deployment workflow.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not modify GitHub repository settings.
- Do not assume local Windows paths exist inside Coder unless documented as operator steps.
- Keep the guide beginner-friendly and command-focused.

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
git log --oneline -10
find . -maxdepth 4 -type f | sort
```

Record key findings in the outbox report.

### 2. Create `docs/resume-from-windows-clone.md`

Create a guide for resuming from a fresh Windows clone.

Include:

- How to verify the Windows clone:
  - `git status`
  - `git branch --show-current`
  - `git remote -v`
  - `git pull --ff-only`
  - `git log --oneline -5`
- How to confirm the repo is at or beyond task 0009.
- How to avoid committing local `.env`, `db/`, `uploads/`, keys, or runtime data.
- When `.env` is needed locally and when it is not.
- That the EC2 deployment path renders `.env` from GitHub Actions secrets/variables, so a Windows local `.env` is not required for deployment.
- How to restart the Coder/Codex workflow at a high level:
  - start/open Coder
  - open or recreate the workspace
  - get a shell inside the workspace
  - clone or pull this repo inside `/home/coder/repo`
  - authenticate Codex if needed
  - run the next inbox prompt
- A PowerShell quick-check section for the Windows clone.
- A Coder workspace quick-check section for the Linux workspace.

Do not include real secrets.

### 3. Create `docs/current-deployment-state.md`

Create a status snapshot document that lists the non-secret current deployment state.

Include:

```text
Repository: scottiepowell/cookbook-roadmaps-link
Branch: main
Public hostname: cookbook.roadmaps.link
Base domain: roadmaps.link
AWS region: us-east-2
EC2 instance ID: i-0bdd490b3a71ccddd
App directory: /opt/cookbook
```

Also include a checklist for control-plane items the operator says are done:

- GitHub variables updated.
- GitHub AWS role secret updated.
- Cloudflare tunnel token secret saved.
- EC2 instance created.

Then include checklist items still to verify:

- EC2 instance has SSM-capable instance profile.
- EC2 appears in Systems Manager Fleet Manager / Managed Nodes.
- Session Manager shell works.
- Bootstrap script runs successfully.
- Preflight script runs successfully.
- GitHub Actions `status` works.
- GitHub Actions `start` works.
- GitHub Actions `deploy` works with `stop_after_deploy=false`.
- Local Compose verification passes.
- Public Cloudflare route verification passes.

### 4. Create `docs/codex-mailbox-continuation.md`

Create a short guide for continuing mailbox work after a Codex timeout or environment restart.

Include:

- How to check whether a task is already done.
- How to inspect `inbox/` and `outbox/`.
- How to verify the last commit.
- How to avoid duplicate work.
- A reusable Codex continuation prompt template.
- A reminder that Codex should not run AWS, Cloudflare, OpenAI, or deployment commands unless the inbox task explicitly says so.

### 5. Update README and first-deploy docs if useful

Add minimal links to the new docs in:

- `README.md`
- `docs/first-deploy-guide.md`
- `docs/repo-map.md`

Only update files where useful.

### 6. Validate locally

Run:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Do not run AWS, Cloudflare, OpenAI, or deployment commands.

### 7. Create outbox report

Create:

```text
outbox/0010-create-local-resume-and-first-deploy-readiness-guide-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 8. Commit changes

If possible, commit with:

```bash
git add docs/resume-from-windows-clone.md docs/current-deployment-state.md docs/codex-mailbox-continuation.md README.md docs/first-deploy-guide.md docs/repo-map.md outbox/0010-create-local-resume-and-first-deploy-readiness-guide-results.md
git commit -m "mailbox: complete task 0010 local resume and first deploy readiness guide"
```

If some documentation files are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `docs/resume-from-windows-clone.md` exists.
- `docs/current-deployment-state.md` exists.
- `docs/codex-mailbox-continuation.md` exists.
- Existing docs link to the new resume/readiness docs where useful.
- The current non-secret deployment state is documented.
- Validation passes locally.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
