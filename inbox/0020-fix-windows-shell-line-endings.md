# Task 0020: Fix Windows shell script line endings

## Goal

Make the repository safe to use from the Windows clone at `C:\Users\scott\cookbook-roadmaps-link` by preventing Bash scripts from being checked out with CRLF line endings. The immediate failure is:

```text
bash scripts/validate-repo.sh
: invalid option name.sh: line 2: set: pipefail
```

This happens when Bash receives `set -euo pipefail` with Windows carriage returns.

## Requirements

1. Add a top-level `.gitattributes` file that forces shell scripts to LF line endings.

   Include at least:

   ```gitattributes
   *.sh text eol=lf
   scripts/* text eol=lf
   deploy.sh text eol=lf
   ```

   You may also include sane defaults for YAML/Markdown/Python if appropriate, but do not create noisy churn.

2. Normalize existing shell scripts to LF in the working tree.

   At minimum verify/fix:

   - `deploy.sh`
   - `scripts/*.sh`

3. Add documentation for Windows users.

   Suggested location:

   - `docs/windows-local-development.md`

   Cover:

   - PowerShell repo path: `C:\Users\scott\cookbook-roadmaps-link`
   - Use `python -m pytest ai-api\tests` for direct tests.
   - Use Git Bash, WSL, or a Bash-compatible shell for `bash scripts/validate-repo.sh`.
   - Why `.gitattributes` forces LF for `.sh` files.
   - PowerShell alternatives such as `Get-Content scripts\validate-repo.sh -TotalCount 5` instead of `head`.

4. Update docs links if useful:

   - `README.md`
   - `docs/repo-map.md`
   - any existing Windows resume/recovery doc if relevant

5. Do not change AI provider behavior, importer behavior, RAG behavior, deployment behavior, or secrets.

6. Run local validation:

   - `python -m pytest ai-api\tests` from the active Windows venv, if available
   - `bash -n scripts/validate-repo.sh`
   - `bash scripts/validate-repo.sh`
   - `git diff --check`
   - `docker compose config --quiet` if Docker Compose is available

7. Create `outbox/0020-fix-windows-shell-line-endings-results.md` with:

   - Summary
   - Files changed
   - Root cause of the `pipefail` error
   - Validation results
   - Any commands that were unavailable
   - Recommended next task

8. Commit and push:

   ```bash
   git add .gitattributes deploy.sh scripts docs README.md outbox/0020-fix-windows-shell-line-endings-results.md
   git commit -m "mailbox: complete task 0020 fix windows shell line endings"
   git push origin main
   ```

## Done Criteria

- `.gitattributes` exists and forces LF for `.sh` files.
- Shell scripts are normalized to LF.
- Windows local-development docs exist.
- AI tests still pass.
- Bash validator no longer fails on `set -euo pipefail` due to CRLF.
- Outbox report exists.
- Changes are committed and pushed.
