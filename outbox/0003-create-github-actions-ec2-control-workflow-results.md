# Task 0003 Results: GitHub Actions EC2 Control Workflow

## Summary

Created a manual GitHub Actions workflow for EC2 status, start, deployment,
container restart, and stop operations. The workflow uses GitHub OIDC for AWS
authentication and AWS Systems Manager Run Command instead of SSH. Added AWS
OIDC/IAM setup guidance and operator documentation. No credentials or secret
values were created or committed.

## Files Created Or Modified

- Created `.github/workflows/cookbook-ec2-control.yml`.
- Created `docs/aws-github-oidc-policy.md`.
- Created `docs/github-actions-deploy-workflow.md`.
- Created `outbox/0003-create-github-actions-ec2-control-workflow-results.md`.

## Repository Inspection

- Working directory: `/home/coder/repo`.
- Branch: `main`.
- Remote: `origin` uses
  `https://github.com/scottiepowell/cookbook-roadmaps-link.git`.
- The working tree was clean before implementation after fast-forwarding to the
  commit that added inbox task 0003.
- Task 0002 runtime files were present, including `docker-compose.yml`,
  `.env.example`, `.gitignore`, `deploy.sh`, and runtime documentation.
- No existing workflow files were present.

## Git Status

- Before: clean `main`, synchronized with `origin/main`.
- After implementation: only the four task 0003 workflow, documentation, and
  report files are added.

## Validation

- `git diff --check` passed.
- `bash -n deploy.sh` passed.
- All eight workflow `run` blocks passed `bash -n` after GitHub expressions
  were replaced with inert validation placeholders. Heredoc boundaries,
  conditionals, quoting, and secret handling were also visually inspected.
- `yamllint` and `actionlint` were unavailable and were not installed, as
  required by the task.
- A content scan found no common static AWS, GitHub, OpenAI, or private-key
  credential formats.
- The IAM policy includes `ec2:DescribeInstanceStatus` in addition to the task's
  base list because the required `instance-status-ok` waiter uses that API; the
  reason is documented in the OIDC policy guide.

## Assumptions

- The public repository can be cloned from the GitHub repository URL without a
  deploy key or token.
- SSM Run Command executes with permission to manage `APP_DIR` and Docker.
- The EC2 image has Git, Docker Engine, Docker Compose, the SSM agent, `base64`,
  and a Bash-compatible shell.
- `restart` means restarting existing Compose services without pulling code or
  replacing `.env`; `deploy` performs the code and configuration update.
- `stop_after_deploy` applies only after a successful `deploy`, matching the
  input name and avoiding surprising stops after `start` or `restart`.

## Blockers

- None during implementation.

## Commit And Push

- Commit message: `mailbox: complete task 0003 github actions ec2 control workflow`.
- Push target: `origin/main`; no pre-push blocker was identified.

## Recommended Next Task

Provision or audit the AWS OIDC provider, workflow IAM role, EC2 instance
profile, Systems Manager connectivity, and Cloudflare Tunnel route. Then add the
documented GitHub settings and perform a manual `status` run before the first
deployment.
