# Task 0012 Results: Fix SSM Script Transport With Base64

## Summary

Task 0011 fixed the original `/bin/sh` `pipefail` failure by wrapping the remote script with `bash -lc`, but the SSM transport still depended on inline shell quoting. The deploy then failed before Bash could run with:

```text
Syntax error: Unterminated quoted string
```

The workflow now transports the deploy and restart Bash script bodies as base64. The command sent to `AWS-RunShellScript` is POSIX-`sh` compatible: it creates a temporary script under `/tmp`, decodes the base64 payload into that file, chmods it, executes it with `bash`, and removes it with a trap.

## Files Changed

- `.github/workflows/cookbook-ec2-control.yml`
- `docs/github-actions-deploy-workflow.md`
- `outbox/0012-fix-ssm-script-transport-with-base64-results.md`

## Transport Confirmation

- Removed `printf 'bash -lc %q'` usage from the workflow.
- No remaining `bash -lc` usage exists in `.github/workflows/cookbook-ec2-control.yml`.
- Deploy now builds `remote_script_payload` with `base64 -w 0`, decodes it to `script_tmp`, and runs `bash "$script_tmp"`.
- Restart now builds `remote_script_payload` with `base64 -w 0`, decodes it to `script_tmp`, and runs `bash "$script_tmp"`.
- Existing `.env` handling is preserved: the workflow still separately base64 encodes the rendered `.env` payload and writes it remotely with mode `0600`.

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
- `base64 --decode`, `mktemp`, `chmod`, and `bash` are available on the Ubuntu EC2 host, consistent with the reported bootstrap and preflight state.
- `base64 -w 0` is available on the GitHub Actions `ubuntu-latest` runner.

## Blockers

None.

## Recommended Next Operator Action

Run the GitHub Actions `deploy` action from the GitHub UI when ready, then inspect the SSM command output to confirm the temporary-script transport reaches Bash and the previous inline quoting error is gone.
