# Resume From A Windows Clone

Use this guide when the repository has been re-cloned on Windows and you need to resume the Coder/Codex workflow for this project.

## Verify The Windows Clone

Open PowerShell in the repository directory:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git status
git branch --show-current
git remote -v
git pull --ff-only
git log --oneline -5
```

Expected results:

- The branch is `main`.
- `origin` points to `https://github.com/scottiepowell/cookbook-roadmaps-link.git`.
- `git status` does not show unreviewed local changes.
- The recent log includes `mailbox: complete task 0009 correct domain to roadmaps link` or a later task completion commit.

If `git pull --ff-only` fails, stop and inspect the local changes before continuing. Do not overwrite local work without understanding it.

## Confirm The Repo Is At Or Beyond Task 0009

Check the mailbox files:

```powershell
Get-ChildItem inbox
Get-ChildItem outbox
git log --oneline -10
```

The repo is at or beyond task 0009 when all of these are true:

- `inbox/0009-correct-domain-to-roadmaps-link.md` exists.
- `outbox/0009-correct-domain-to-roadmaps-link-results.md` exists.
- `git log --oneline -10` shows `mailbox: complete task 0009 correct domain to roadmaps link` or a later completion commit.

## Avoid Committing Local Runtime Data

Never commit real secrets or runtime data. Before every commit, run:

```powershell
git status --short
git diff --cached --name-only
```

Do not add or commit:

- `.env`
- `.env.*` except `.env.example`
- `db/`
- `uploads/`
- private keys such as `*.pem` or `*.key`
- Terraform state such as `*.tfstate`
- generated runtime logs, database files, uploads, backups, or credentials

The repository `.gitignore` already excludes the main local secret and runtime paths. Still check staged files before every commit.

## When A Local `.env` Is Needed

A local `.env` is only needed when you intentionally run the app locally or perform local Compose verification that needs runtime configuration. Keep it untracked and do not paste its contents into prompts, issues, logs, or reports.

A Windows local `.env` is not required for EC2 deployment. The EC2 deployment path renders the host `.env` from GitHub Actions secrets and variables during the deployment workflow.

## Restart Coder And Codex

Use this high-level sequence after a restart or timeout:

1. Start or open Coder.
2. Open the existing workspace, or recreate it if needed.
3. Open a shell inside the Coder workspace.
4. Clone or pull this repository inside `/home/coder/repo`.
5. Authenticate Codex if the workspace no longer has a valid session.
6. Read the next numbered `inbox/` prompt.
7. Let Codex implement the task, validate locally, write the matching `outbox/` report, and commit the result.

Inside the Coder workspace, use the Linux path:

```bash
cd /home/coder/repo
git status
git pull --ff-only
```

Do not assume the Windows path exists inside Coder. Treat `C:\Users\scott\cookbook-roadmaps-link` as the Windows clone and `/home/coder/repo` as the Coder workspace clone.

## PowerShell Quick Check

Run this from Windows:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git status --short --branch
git branch --show-current
git remote -v
git log --oneline -5
Get-ChildItem inbox | Sort-Object Name | Select-Object -Last 5
Get-ChildItem outbox | Sort-Object Name | Select-Object -Last 5
```

Confirm the branch, remote, latest task files, and clean working tree before asking Codex to continue.

## Coder Workspace Quick Check

Run this inside the Coder Linux workspace:

```bash
cd /home/coder/repo
pwd
ls -la
git status --short --branch
git branch --show-current
git remote -v
git pull --ff-only
git log --oneline -5
find inbox outbox -maxdepth 1 -type f | sort | tail -20
```

If the Coder clone is behind the Windows clone or GitHub, pull before starting the next mailbox task. If it has local changes, inspect them before continuing.
