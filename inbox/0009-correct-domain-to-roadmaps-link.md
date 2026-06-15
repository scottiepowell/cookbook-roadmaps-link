# Task 0009: Correct target domain to roadmaps.link

## Goal

Correct the project target domain from the old value:

```text
cookbook.roadmap.links
```

to the real Cloudflare domain and hostname:

```text
cookbook.roadmaps.link
```

This task should update repository documentation, examples, validation rules, and runtime templates only. Do not create cloud resources, do not run AWS or Cloudflare commands, and do not commit secrets.

## Project context

The real domain is:

```text
roadmaps.link
```

The real application hostname should be:

```text
cookbook.roadmaps.link
```

Cloudflare Tunnel has been started and the GitHub variable and secret setup has begun. The repo still contains earlier references to the incorrect hostname `cookbook.roadmap.links`. Those must be corrected before EC2 deployment to avoid origin, DNS, and documentation mismatch.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not modify GitHub repository settings from this task.
- Do not include any real Cloudflare tunnel token or AWS account ID.
- Use `cookbook.roadmaps.link` everywhere the public app hostname is intended.
- Use `roadmaps.link` where the base domain is intended.
- Keep old task history readable where possible, but add a clear correction if old inbox/outbox history is intentionally not rewritten.

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
find . -maxdepth 4 -type f | sort
```

Record key findings in the outbox report.

### 2. Find all old-domain references

Run a search similar to:

```bash
grep -RIn "cookbook\.roadmap\.links\|roadmap\.links" . \
  --exclude-dir=.git \
  --exclude-dir=db \
  --exclude-dir=uploads || true
```

Record a summary in the outbox report.

### 3. Update active project files

Update active configuration, examples, and documentation to use:

```text
https://cookbook.roadmaps.link
cookbook.roadmaps.link
roadmaps.link
```

Expected files likely include, but are not limited to:

- `README.md`
- `.env.example`
- `docs/architecture.md`
- `docs/first-deploy-guide.md`
- `docs/runtime-scaffold.md`
- `docs/cloudflare-tunnel-setup.md`
- `docs/github-actions-deploy-workflow.md`
- `docs/github-settings-checklist.md`
- `docs/ec2-runtime-bootstrap.md`
- `docs/operations-runbook.md`
- any relevant scripts that default to the public hostname

Do not edit generated runtime data. Do not add secrets.

### 4. Handle historical mailbox files carefully

The `inbox/` and `outbox/` folders contain task history. It is acceptable to leave old historical task specs unchanged if rewriting history would create confusion, but the current operational docs and templates must be corrected.

Create a short note in the outbox report explaining whether historical inbox/outbox files were left as-is or corrected.

If you leave old references in historical mailbox files, update validation so active files are guarded without failing on old historical records.

### 5. Update repository validation guard

Update `scripts/validate-repo.sh` so future active documentation and configuration do not accidentally reintroduce the old hostname.

Requirements:

- The validator should fail if active files contain `cookbook.roadmap.links` or `roadmap.links` where the old domain appears.
- The validator may exclude `inbox/` and `outbox/` history from this specific old-domain rule if the history is intentionally preserved.
- The failure message should print filenames only, not secret values.
- Keep the existing validation behavior intact.

Update `docs/repo-validation.md` to mention the domain guard.

### 6. Update first-deploy guidance

Make sure `docs/first-deploy-guide.md` and `docs/github-settings-checklist.md` clearly state that GitHub Actions variables should use:

```text
ORIGIN=https://cookbook.roadmaps.link
DOMAIN=cookbook.roadmaps.link
APP_DIR=/opt/cookbook
```

### 7. Validate locally

Run:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Also run a final active-file grep to confirm no old active reference remains. Example:

```bash
grep -RIn "cookbook\.roadmap\.links\|roadmap\.links" . \
  --exclude-dir=.git \
  --exclude-dir=inbox \
  --exclude-dir=outbox \
  --exclude-dir=db \
  --exclude-dir=uploads || true
```

Do not run AWS, Cloudflare, OpenAI, or deployment commands.

### 8. Create outbox report

Create:

```text
outbox/0009-correct-domain-to-roadmaps-link-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Old-domain search results summary.
- Whether historical inbox/outbox files were preserved or edited.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 9. Commit changes

If possible, commit with:

```bash
git add .env.example README.md docs scripts outbox/0009-correct-domain-to-roadmaps-link-results.md
git commit -m "mailbox: complete task 0009 correct domain to roadmaps link"
```

If some paths are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- Active project docs and examples use `cookbook.roadmaps.link`.
- Active project docs and examples use `roadmaps.link` as the base domain where needed.
- GitHub variable guidance shows `ORIGIN=https://cookbook.roadmaps.link`.
- GitHub variable guidance shows `DOMAIN=cookbook.roadmaps.link`.
- Repository validation guards against reintroducing the old domain in active files.
- The outbox report documents how historical mailbox records were handled.
- Validation passes locally.
- Changes are committed and pushed if possible.
- No secrets are committed.
