# Windows Local Development

Use this guide when working from the Windows clone at:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
```

## Shells

Use PowerShell for Windows-native inspection and Git commands:

```powershell
git status --short --branch
git pull --ff-only
Get-Content scripts\validate-repo.sh -TotalCount 5
```

Use Git Bash, WSL, or another Bash-compatible shell for repository shell scripts:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
```

PowerShell does not provide every common Unix helper. Prefer PowerShell equivalents when you are already in PowerShell; for example, use `Get-Content scripts\validate-repo.sh -TotalCount 5` instead of `head`.

## Python Tests

If the active Windows Python environment has test dependencies installed, run:

```powershell
python -m pytest ai-api\tests
```

If `pytest` is unavailable in the active environment, run the repository validator from a Bash-compatible shell. It creates a temporary virtual environment and installs `ai-api/requirements.txt` before running the AI API tests.

## Shell Script Line Endings

Bash scripts must use LF line endings. If a script is checked out with CRLF, Bash can read a carriage return as part of a command or option. One common symptom is:

```text
: invalid option name.sh: line 2: set: pipefail
```

The top-level `.gitattributes` file forces LF for shell scripts:

```gitattributes
*.sh text eol=lf
scripts/* text eol=lf
deploy.sh text eol=lf
```

After changing `.gitattributes`, normalize shell scripts before committing and verify with:

```powershell
git diff --check
bash -n scripts/validate-repo.sh
```

Do not change deployment behavior, runtime secrets, or AI provider settings when fixing line endings.

## Start the public Cookbook stack from Git Bash

The checked-in launcher starts Docker Desktop when needed, waits for its Linux
engine, validates the existing ignored environment files, and starts the public
core, AI sidecar, and existing Cloudflare connector:

```bash
cd /c/Users/scott/cookbook-roadmaps-link
./scripts/start-public-cookbook.sh
```

The external core defaults to
`$HOME/projects/vanilla-cookbook-core`. Override `COOKBOOK_CORE_DIR` only when
that checkout is elsewhere. The launcher reports bounded container and HTTP
status; it does not print environment contents or make AI provider calls.

If Docker Desktop exits with an inaccessible `dockerInference` socket, the
Windows WSL service still owns a stale Docker runtime entry. Restart Windows,
then run the launcher again. An administrator can instead restart `WslService`;
the launcher deliberately does not elevate or delete runtime state itself.
