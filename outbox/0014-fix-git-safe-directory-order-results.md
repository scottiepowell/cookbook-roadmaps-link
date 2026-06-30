# Task 0014 Results: Fix Git Safe Directory Order

## Summary

The deploy remote Bash script had a valid `HOME`, but Git failed on an existing `/opt/cookbook` checkout with:

```text
fatal: detected dubious ownership in repository at '/opt/cookbook'
```

The workflow now adds a scoped Git `safe.directory` exception for `$app_dir` before any `git -C "$app_dir"` command touches an existing checkout. The existing scoped safe-directory line before `.env` rendering and `./deploy.sh` was kept, with `|| true`, so `deploy.sh` also runs after the scoped exception has been applied.

## Files Changed

- `.github/workflows/cookbook-ec2-control.yml`
- `docs/github-actions-deploy-workflow.md`
- `outbox/0014-fix-git-safe-directory-order-results.md`

## Safe Directory Confirmation

- Deploy configures `git config --global --add safe.directory "$app_dir" || true` immediately after `install -d -m 0755 "$app_dir"`.
- That scoped configuration now runs before `git -C "$app_dir" remote set-url origin "$repository_url"`.
- That scoped configuration now runs before `git -C "$app_dir" checkout main`.
- The workflow does not add `safe.directory '*'` or any wildcard safe-directory exception.

## Preserved Behavior

- The task 0012 base64 SSM script transport remains in place.
- The task 0013 `HOME` and `XDG_CONFIG_HOME` initialization remains in place before Git, Docker, or config-path-sensitive commands.
- Secret-safe `.env` handling is preserved: the workflow still separately base64 encodes the rendered `.env` payload and writes it remotely with mode `0600`.

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
- Git's dubious-ownership failure occurs only when `$app_dir/.git` already exists and is owned differently than the SSM command user.
- Keeping the safe-directory exception scoped to `$app_dir` is sufficient for both the workflow's Git commands and `deploy.sh`.

## Blockers

None.

## Recommended Next Operator Action

Run the GitHub Actions `deploy` action from the GitHub UI when ready, then inspect the SSM output to confirm Git no longer fails with the dubious-ownership safe-directory error.
