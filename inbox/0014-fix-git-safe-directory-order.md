# Task 0014: Fix Git Safe Directory Order

## Goal

Fix the GitHub Actions deployment workflow so Git's `safe.directory` exception is configured before any Git command runs against `/opt/cookbook`.

The deploy now reaches the remote Bash script and has a valid `HOME`, but it fails with:

```text
fatal: detected dubious ownership in repository at '/opt/cookbook'
To add an exception for this directory, call:

    git config --global --add safe.directory /opt/cookbook
failed to run commands: exit status 128
```

The current workflow adds safe.directory only after it has already run Git commands against `$app_dir`:

```bash
if [[ -d "$app_dir/.git" ]]; then
  git -C "$app_dir" remote set-url origin "$repository_url"
  git -C "$app_dir" checkout main
elif ...
  git clone ... "$app_dir"
fi
git config --global --add safe.directory "$app_dir"
```

This order is wrong for an existing checkout that may be owned by `ubuntu` while the SSM command runs as `root`.

## Current environment

- Repository: `scottiepowell/cookbook-roadmaps-link`
- Branch: `main`
- AWS region: `us-east-2`
- Current EC2 instance ID: `i-0e5458adbc0663914`
- EC2 is Online in Systems Manager Fleet Manager.
- Manual EC2 bootstrap/preflight passed.
- GitHub Actions `status` passed.
- Deploy now reaches the remote Bash script and prints: `Remote runtime: user=root, home=/root`.
- Failure is now Git safe-directory protection on `/opt/cookbook`.

## Important rules

- Do not commit secrets.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not change GitHub repository settings.
- Only modify repo files and local validation/docs as needed.

## Required fix

Update `.github/workflows/cookbook-ec2-control.yml` so `git config --global --add safe.directory "$app_dir"` is run before any `git -C "$app_dir" ...` command when `$app_dir/.git` exists.

Suggested implementation in the deploy remote script:

```bash
app_dir='<APP_DIR substituted by workflow>'
repository_url='<REPOSITORY_URL substituted by workflow>'
install -d -m 0755 "$app_dir"
if [[ -d "$app_dir/.git" ]]; then
  git config --global --add safe.directory "$app_dir" || true
  git -C "$app_dir" remote set-url origin "$repository_url"
  git -C "$app_dir" checkout main
elif [[ -z "$(find "$app_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  git clone --branch main --single-branch "$repository_url" "$app_dir"
  git config --global --add safe.directory "$app_dir" || true
else
  echo "APP_DIR exists but is not an empty directory or Git checkout" >&2
  exit 1
fi
```

Then keep the existing `.env` writing and `./deploy.sh` behavior.

Also consider adding this before `./deploy.sh` because `deploy.sh` runs `git pull --ff-only` from `/opt/cookbook`:

```bash
git config --global --add safe.directory "$app_dir" || true
```

Do not add a wildcard safe directory. Keep it scoped to `$app_dir`.

## Optional ownership hardening

If needed, ensure `/opt/cookbook` remains writable by the runtime user and usable by the SSM command. Do not chown blindly unless the existing docs/scripts already use that ownership model and the change is justified.

## Documentation update

Update the SSM/GitHub Actions troubleshooting documentation, likely `docs/github-actions-deploy-workflow.md`, to add:

- Symptom: `fatal: detected dubious ownership in repository at '/opt/cookbook'`.
- Cause: SSM command runs as one user while the repo may be owned by another user.
- Fix: workflow adds a scoped `safe.directory` exception for `/opt/cookbook` before any Git command touches the checkout.

## Validation

Run local validation only:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Also inspect the workflow and confirm:

- In the deploy remote script, safe.directory is configured before `git -C "$app_dir" ...` commands.
- The safe.directory value is scoped to `$app_dir`, not `*`.
- The task 0012 base64 script transport remains in place.
- The task 0013 HOME initialization remains in place.
- No secrets are printed or committed.

Do not run AWS, Cloudflare, OpenAI, or deployment commands as part of this task.

## Outbox report

Create:

```text
outbox/0014-fix-git-safe-directory-order-results.md
```

Include:

- Summary of the new failure and fix.
- Files changed.
- Exact validation commands run.
- Confirmation that deploy configures safe.directory before Git touches the existing checkout.
- Confirmation that base64 script transport and HOME initialization remain in place.
- Any assumptions.
- Any blockers.
- Recommended next operator action.

## Commit

Commit with:

```bash
git add .github/workflows/cookbook-ec2-control.yml docs/ outbox/0014-fix-git-safe-directory-order-results.md
git commit -m "mailbox: complete task 0014 fix git safe directory order"
```

If only a subset of docs changed, stage only actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- Deploy configures `safe.directory` before any Git command touches an existing `/opt/cookbook` checkout.
- The safe.directory value is scoped to `$app_dir`, not wildcarded.
- Secret-safe `.env` rendering behavior is preserved.
- Base64 SSM script transport remains intact.
- HOME/XDG_CONFIG_HOME initialization remains intact.
- Documentation explains the Git dubious-ownership failure mode.
- Local validation passes.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
