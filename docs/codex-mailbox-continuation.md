# Codex Mailbox Continuation

Use this when Codex times out, the workspace restarts, or you need to continue mailbox work without duplicating a completed task.

## Check Whether A Task Is Done

From the repo root:

```bash
git status --short --branch
git log --oneline -10
ls -la inbox outbox
```

A task is usually done when:

- The matching `outbox/<task-name>-results.md` exists.
- The recent Git log contains a completion commit for that task.
- `git status` is clean, or only unrelated local files remain.
- The outbox report says validation passed or clearly documents any blocker.

## Inspect Inbox And Outbox

List task prompts and reports:

```bash
find inbox -maxdepth 1 -type f | sort
find outbox -maxdepth 1 -type f | sort
```

Read the target prompt before acting:

```bash
sed -n '1,240p' inbox/0010-create-local-resume-and-first-deploy-readiness-guide.md
```

Read the matching report if it exists:

```bash
sed -n '1,240p' outbox/0010-create-local-resume-and-first-deploy-readiness-guide-results.md
```

## Verify The Last Commit

```bash
git show --stat --oneline --decorate -1
git show --name-only --oneline -1
```

Confirm the latest commit matches the last completed mailbox task. If the task was committed, do not redo it unless the new prompt explicitly asks for corrections.

## Avoid Duplicate Work

Before editing:

- Compare the target `inbox/` prompt with the matching `outbox/` report.
- Check whether the required files already exist.
- Check whether the latest commit already completed the task.
- If partial work exists, continue from the current files instead of recreating them.
- Do not delete or rewrite unrelated user changes.

## Continuation Prompt Template

```text
Read inbox/<task-file>.md and continue the task from the current repository state.
First check whether it is already complete by inspecting git status, the latest commits,
and the matching outbox report. If work remains, finish it exactly, validate locally,
update the outbox report, and commit the changes. Do not commit secrets. Do not run AWS,
Cloudflare, OpenAI, or deployment commands unless this inbox task explicitly says to.
```

## Command Restrictions

Codex should not run AWS, Cloudflare, OpenAI, or deployment commands unless the active inbox task explicitly permits them. For documentation and readiness tasks, use local Git, shell, validation, and file inspection commands only.
