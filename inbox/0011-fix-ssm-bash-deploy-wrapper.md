# Task 0011: Fix SSM Bash Deploy Wrapper

## Goal

Fix the GitHub Actions deployment workflow so Systems Manager runs the remote deploy and restart payloads with Bash, not `/bin/sh`.

The current `deploy` action reaches AWS and Systems Manager successfully, but the SSM command fails immediately on Ubuntu with:

```text
/var/lib/amazon/ssm/.../_script.sh: 1: set: Illegal option -o pipefail
failed to run commands: exit status 2
```

This means the remote payload is being interpreted by POSIX `sh`/dash, while the payload uses Bash-only syntax such as:

- `set -euo pipefail`
- `[[ ... ]]`
- Bash traps/conditionals

AWS Systems Manager `AWS-RunShellScript` accepts command strings to run on Linux managed instances. The workflow must explicitly invoke Bash for scripts that require Bash.

## Current environment

- Repository: `scottiepowell/cookbook-roadmaps-link`
- Branch: `main`
- AWS region: `us-east-2`
- Current EC2 instance ID: `i-0e5458adbc0663914`
- Systems Manager Fleet Manager shows the instance as Online.
- Manual EC2 bootstrap and preflight already passed:
  - Ubuntu 24.04.4 LTS
  - Docker active
  - Docker Compose available
  - SSM Agent active
  - `/opt/cookbook` exists and is writable by `ubuntu`
  - outbound HTTPS to GitHub works
  - port 3000 warning is expected before deployment

## Important rules

- Do not commit secrets.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not change GitHub repository settings.
- Only modify repo files and validation/docs as needed.

## Required fix

Update `.github/workflows/cookbook-ec2-control.yml` so the remote Systems Manager command for `deploy` runs under Bash.

Preferred implementation:

1. Build the existing remote payload as a Bash script body.
2. Wrap it before passing it to SSM so the command string starts with a POSIX-compatible invocation such as:

   ```bash
   bash -lc '<safely quoted bash script body>'
   ```

   or write the body to a temporary script on the instance and run:

   ```bash
   bash /tmp/<script-name>.sh
   ```

3. Keep secret handling safe. Do not echo secrets. Continue base64 encoding the rendered `.env` payload as the current workflow does.
4. Preserve the current behavior of cloning/updating `$APP_DIR`, writing `$APP_DIR/.env`, and running `./deploy.sh`.
5. Ensure the implementation is robust against quote characters and line breaks in the script body.

Also update the `restart` action remote payload, because it also currently starts with `set -euo pipefail` and uses Bash-style execution assumptions.

## Suggested safe pattern

One acceptable pattern is:

```bash
remote_script="$(cat <<'REMOTE_SCRIPT'
set -euo pipefail
# existing remote script body here
REMOTE_SCRIPT
)"

remote_command="$(printf 'bash -lc %q' "$remote_script")"
```

Then pass `remote_command` into the existing `jq -n --arg command "$remote_command" '{commands: [$command]}'` step.

Adjust quoting carefully so GitHub-side variables that must be substituted by the runner still get substituted, while EC2-side variables remain escaped for the remote shell.

## Documentation/troubleshooting updates

Add a short troubleshooting note to one appropriate docs file, such as `docs/github-actions-deploy-workflow.md` or `docs/operations-runbook.md`, explaining:

- Symptom: `set: Illegal option -o pipefail` in SSM output.
- Cause: remote SSM payload ran under `/bin/sh` instead of Bash.
- Fix: workflow wraps remote deploy/restart payloads with Bash.

## Validation

Run local validation only:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Also inspect the workflow YAML enough to confirm the deploy and restart SSM commands now explicitly invoke Bash.

Do not run AWS, Cloudflare, OpenAI, or deployment commands as part of this task.

## Outbox report

Create:

```text
outbox/0011-fix-ssm-bash-deploy-wrapper-results.md
```

Include:

- Summary of the failure and fix.
- Files changed.
- Exact validation commands run.
- Whether deploy and restart SSM payloads now explicitly invoke Bash.
- Any assumptions.
- Any blockers.
- Recommended next operator action.

## Commit

Commit with:

```bash
git add .github/workflows/cookbook-ec2-control.yml docs/ outbox/0011-fix-ssm-bash-deploy-wrapper-results.md
git commit -m "mailbox: complete task 0011 fix ssm bash deploy wrapper"
```

If only a subset of docs changed, stage only the actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- The deploy SSM remote command explicitly runs under Bash.
- The restart SSM remote command explicitly runs under Bash.
- The workflow still preserves existing secret-safe `.env` rendering behavior.
- A troubleshooting note is documented.
- Local validation passes.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
