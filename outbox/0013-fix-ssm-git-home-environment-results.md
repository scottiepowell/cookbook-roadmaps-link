# Task 0013 Results: Fix SSM Git HOME Environment

## Summary

After the task 0012 base64 script transport fix, the deploy reached the decoded remote Bash script but failed at Git with:

```text
fatal: $HOME not set
```

The deploy and restart remote Bash scripts now initialize `HOME` and `XDG_CONFIG_HOME` immediately after `set -euo pipefail`, before Git, Docker, or config-path-sensitive commands run. The block resolves `HOME` from the current user passwd entry when possible, falls back to `/root`, exports `XDG_CONFIG_HOME`, creates both directories, and prints a non-secret runtime diagnostic.

## Files Changed

- `.github/workflows/cookbook-ec2-control.yml`
- `docs/github-actions-deploy-workflow.md`
- `outbox/0013-fix-ssm-git-home-environment-results.md`

## HOME Initialization Confirmation

- Deploy remote script initializes `HOME` and `XDG_CONFIG_HOME` before `git -C`, `git clone`, or `git config`.
- Restart remote script initializes `HOME` and `XDG_CONFIG_HOME` before `cd`, `docker compose restart`, or `docker compose ps`.
- The diagnostic line only prints the remote username or UID and resolved home path. It does not print secrets, `.env`, tokens, GitHub contexts, or AWS credentials.

## Base64 Transport Confirmation

- The task 0012 base64 script transport remains in place.
- Deploy still builds `remote_script_payload` with `base64 -w 0`, decodes it into a temporary `/tmp/cookbook-ssm.XXXXXX.sh` script, chmods it, and runs `bash "$script_tmp"`.
- Restart uses the same base64 decode-to-temp-script transport and runs `bash "$script_tmp"`.
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
- `getent`, `id`, `mkdir`, `base64 --decode`, `mktemp`, `chmod`, and `bash` are available on the Ubuntu EC2 host, consistent with the reported bootstrap and preflight state.
- The remote SSM command may have a sparse environment, so the remote Bash script must not rely on an inherited `HOME`.

## Blockers

None.

## Recommended Next Operator Action

Run the GitHub Actions `deploy` action from the GitHub UI when ready, then inspect the SSM output to confirm Git no longer fails with `fatal: $HOME not set`.
