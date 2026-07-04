# Task 0020 Results: Fix Windows Shell Script Line Endings

## Summary

Added repository line-ending rules and normalized the tracked shell scripts so Windows checkouts keep Bash scripts as LF. Added Windows local-development documentation for PowerShell, Git Bash or WSL usage, Python tests, and shell-script validation.

No AI provider behavior, importer behavior, RAG behavior, deployment behavior, or secrets were changed.

## Files Changed

- `.gitattributes`
- `deploy.sh`
- `scripts/*.sh`
- `docs/windows-local-development.md`
- `docs/resume-from-windows-clone.md`
- `docs/repo-map.md`
- `README.md`
- `outbox/0020-fix-windows-shell-line-endings-results.md`

## Root Cause

The Windows working tree had `deploy.sh` and `scripts/*.sh` checked out with CRLF line endings. Bash can treat the carriage return as part of a command or option, so `set -euo pipefail` may be parsed with a hidden `\r`, producing errors like:

```text
: invalid option name.sh: line 2: set: pipefail
```

The new `.gitattributes` forces LF for shell scripts:

```gitattributes
*.sh text eol=lf
scripts/* text eol=lf
deploy.sh text eol=lf
```

`git ls-files --eol deploy.sh scripts/*.sh` reports `i/lf w/lf attr/text eol=lf` for all tracked shell scripts after normalization.

## Validation Results

```bash
python -m pytest ai-api\tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `python -m pytest ai-api\tests`: unavailable in the active Windows Python because `pytest` is not installed.
- `bash -n scripts/validate-repo.sh`: default `bash` is WSL-backed in this shell and failed with `E_ACCESSDENIED`; Git Bash equivalent passed.
- `bash scripts/validate-repo.sh`: default `bash` is WSL-backed in this shell and failed with `E_ACCESSDENIED`; Git Bash equivalent passed.
- `git diff --check`: passed. Git emitted expected Windows CRLF warnings for Markdown files.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.
- `C:\Program Files\Git\bin\bash.exe scripts/validate-repo.sh`: passed.
  - Shell script syntax: PASS
  - Docker Compose configuration: PASS
  - AI API tests: PASS, `26 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS

## Commands Unavailable

- Direct `python -m pytest ai-api\tests` was unavailable because the active Windows interpreter does not have `pytest`.
- The unqualified `bash` command maps to a blocked WSL path in this environment. Git Bash works and is documented for Windows local development.

## Recommended Next Task

Proceed with the next mailbox task after pulling `main` in any other clone. For future Windows work, keep shell-script changes behind `.gitattributes` and validate with Git Bash.
