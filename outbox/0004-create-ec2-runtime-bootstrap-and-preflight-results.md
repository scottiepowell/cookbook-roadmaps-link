# Task 0004 Results: EC2 Runtime Bootstrap And Preflight

## Summary

Created idempotent Ubuntu EC2 bootstrap and preflight scripts, documented the
manual host preparation path, and added a first-deployment GitHub settings
checklist. The assets prepare Git, Docker, Docker Compose, AWS SSM Agent, and
`/opt/cookbook` without creating cloud resources or writing application
secrets.

## Files Created Or Modified

- Created `scripts/bootstrap-ec2-runtime.sh`.
- Created `scripts/preflight-ec2-runtime.sh`.
- Created `docs/ec2-runtime-bootstrap.md`.
- Created `docs/github-settings-checklist.md`.
- Updated `docs/github-actions-deploy-workflow.md` with links to the new guides.
- Created `outbox/0004-create-ec2-runtime-bootstrap-and-preflight-results.md`.

## Repository Inspection

- Working directory: `/home/coder/repo`.
- Branch: `main`.
- Remote: `origin` uses
  `https://github.com/scottiepowell/cookbook-roadmaps-link.git`.
- The working tree was clean and synchronized with `origin/main` after
  fast-forwarding to the commit that added inbox task 0004.
- Runtime Compose, deployment, OIDC, and GitHub Actions workflow assets from
  tasks 0002 and 0003 were present.
- No `scripts/` directory or EC2 bootstrap/preflight assets existed.

## Git Status

- Before: clean `main`, synchronized with `origin/main`.
- After implementation: only the six task 0004 scripts, documentation, and
  report paths are changed or added.

## Validation

- `git diff --check` passed.
- `bash -n` passed for `deploy.sh`, `scripts/bootstrap-ec2-runtime.sh`,
  and `scripts/preflight-ec2-runtime.sh`.
- `shellcheck` was unavailable and was not installed, as required by the task.
- Both new scripts were verified as executable.
- A non-destructive local preflight completed with a final summary of 8 passes, 1 warning, and 2 failures before returning nonzero. The expected failures were the absence
  of a systemd Docker service and SSM Agent in the development container.
- Required package, service, app-directory, HTTPS, and port checks were reviewed.
- A content scan found no common static AWS, GitHub, OpenAI, or private-key
  credential formats.

## Assumptions

- The future host uses a current Ubuntu Server release with APT, systemd, and
  snap support.
- The intended runtime user is an existing non-root account, normally `ubuntu`.
- Installing Ubuntu's `docker.io` package is acceptable for this lab, with an
  available Compose package selected from the configured Ubuntu repositories.
- The EC2 instance profile and outbound network path needed for SSM registration
  are configured outside these scripts.
- The scripts are reviewed or transferred to the host before the repository is
  first cloned into `/opt/cookbook` by the deployment workflow.

## Blockers

- None during implementation.

## Commit And Push

- Commit message: `mailbox: complete task 0004 ec2 runtime bootstrap and preflight`.
- Push target: `origin/main`; no pre-push blocker was identified.

## Recommended Next Task

Run the reviewed bootstrap and preflight scripts on the provisioned Ubuntu EC2
instance, configure the documented GitHub and Cloudflare settings, then execute
the workflow's `status`, `start`, and first `deploy` actions in order.
