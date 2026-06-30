# Task 0011 Results: Fix SSM Bash Deploy Wrapper

## Summary

The GitHub Actions `deploy` and `restart` actions sent Bash-style remote script bodies directly to `AWS-RunShellScript`. On Ubuntu, Systems Manager can run those command strings under `/bin/sh`, which caused this failure:

```text
set: Illegal option -o pipefail
```

The workflow now builds each remote payload as `remote_script`, then wraps it with:

```bash
remote_command="$(printf 'bash -lc %q' "$remote_script")"
```

The SSM parameter payload still passes a single command through `jq`, but that command now explicitly invokes Bash before evaluating the remote script body.

## Files Changed

- `.github/workflows/cookbook-ec2-control.yml`
- `docs/github-actions-deploy-workflow.md`
- `outbox/0011-fix-ssm-bash-deploy-wrapper-results.md`

## SSM Bash Wrapper Confirmation

- Deploy payload: explicitly invokes `bash -lc` before being sent to `AWS-RunShellScript`.
- Restart payload: explicitly invokes `bash -lc` before being sent to `AWS-RunShellScript`.
- Existing `.env` handling is preserved: the workflow still renders the environment payload in memory, base64 encodes it, writes it to a temporary remote file, moves it to `$APP_DIR/.env`, and sets mode `0600`.

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

- This session is attached to the Windows clone at `C:\Users\scott\cookbook-roadmaps-link`; `/home/coder/repo` remains the documented Coder workspace path.
- The runner shell for GitHub Actions steps is Bash on `ubuntu-latest`, so `printf %q` is available when constructing the SSM command string.
- The workflow input validation continues to constrain `APP_DIR` to safe absolute path characters.

## Blockers

None.

## Recommended Next Operator Action

Run the GitHub Actions `restart` or `deploy` action from the GitHub UI when ready, then inspect the SSM command output to confirm the previous `/bin/sh` `pipefail` error is gone.
