# Task 0013: Fix SSM Git HOME Environment

## Goal

Fix the GitHub Actions deployment workflow so Git commands run correctly under the sparse noninteractive environment provided by Systems Manager.

After task 0012, the Bash script transport works and the deploy now reaches the actual remote script. The current deploy failure is:

```text
Cloning into '/opt/cookbook'...
fatal: $HOME not set
failed to run commands: exit status 128
```

This means the SSM remote command environment does not provide `HOME`, and Git requires a valid home/config location during clone/config operations.

## Current environment

- Repository: `scottiepowell/cookbook-roadmaps-link`
- Branch: `main`
- AWS region: `us-east-2`
- Current EC2 instance ID: `i-0e5458adbc0663914`
- EC2 is Online in Systems Manager Fleet Manager.
- Manual EC2 bootstrap/preflight passed.
- GitHub Actions `status` passed.
- Deploy now reaches the base64-decoded Bash script, then fails at `git clone` because `$HOME` is not set.

## Important rules

- Do not commit secrets.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not change GitHub repository settings.
- Only modify repo files and local validation/docs as needed.

## Required fix

Update `.github/workflows/cookbook-ec2-control.yml` so the remote Bash scripts initialize a valid `HOME` before any command that may use Git, Docker, or user config paths.

Add a robust block near the top of both remote Bash scripts, immediately after `set -euo pipefail`, before `git`, `cd`, or `docker compose` commands.

Suggested implementation:

```bash
if [[ -z "${HOME:-}" ]]; then
  home_from_passwd="$(getent passwd "$(id -u)" | cut -d: -f6 || true)"
  if [[ -n "$home_from_passwd" ]]; then
    export HOME="$home_from_passwd"
  else
    export HOME=/root
  fi
fi
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
mkdir -p "$HOME" "$XDG_CONFIG_HOME"
```

Because this block is inside a GitHub Actions heredoc that builds a remote script, ensure variables intended for the EC2 runtime are escaped correctly as needed. The generated remote script should contain runtime Bash expressions, not accidentally expanded by the GitHub runner.

Apply this to both:

- deploy action remote script
- restart action remote script

## Optional hardening

If useful, also add a small diagnostic line that does not expose secrets, for example:

```bash
echo "Remote runtime: user=$(id -un 2>/dev/null || id -u), home=$HOME"
```

Do not echo environment variables, tokens, `.env`, GitHub contexts, or AWS credentials.

## Documentation update

Update the SSM troubleshooting documentation, likely `docs/github-actions-deploy-workflow.md`, to add:

- Symptom: `fatal: $HOME not set` during `git clone` or `git config`.
- Cause: Systems Manager remote command sessions can have a sparse environment.
- Fix: workflow initializes `HOME` and `XDG_CONFIG_HOME` inside the remote Bash payload before Git runs.

## Validation

Run local validation only:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Also inspect the workflow and confirm:

- deploy remote script initializes `HOME` before `git clone`, `git -C`, or `git config`.
- restart remote script initializes `HOME` before Docker/Compose or any config-path-sensitive command.
- the task 0012 base64 script transport remains in place.
- no secrets are printed or committed.

Do not run AWS, Cloudflare, OpenAI, or deployment commands as part of this task.

## Outbox report

Create:

```text
outbox/0013-fix-ssm-git-home-environment-results.md
```

Include:

- Summary of the new failure and fix.
- Files changed.
- Exact validation commands run.
- Confirmation that deploy and restart initialize `HOME`.
- Confirmation that base64 script transport remains in place.
- Any assumptions.
- Any blockers.
- Recommended next operator action.

## Commit

Commit with:

```bash
git add .github/workflows/cookbook-ec2-control.yml docs/ outbox/0013-fix-ssm-git-home-environment-results.md
git commit -m "mailbox: complete task 0013 fix ssm git home environment"
```

If only a subset of docs changed, stage only actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- Deploy remote script initializes `HOME` before Git runs.
- Restart remote script initializes `HOME` before Docker/Compose runs.
- The task 0012 base64 transport remains intact.
- Secret-safe `.env` rendering behavior is preserved.
- Documentation explains the `$HOME not set` failure mode.
- Local validation passes.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
