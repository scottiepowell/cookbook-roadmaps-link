---
name: mailbox-gitops
description: Execute repository inbox Markdown prompts through an Issue, branch, validation, outbox result, and PR delivery workflow. Use for mailbox task execution or maintaining inbox/outbox GitOps; respect the selected repository and explicit stop boundaries.
---

# Mailbox GitOps

Treat inbox as the durable queue and outbox as an evidence record. Follow the
current AGENTS.md and repository ownership boundaries. This method does not
authorize unrelated work or external actions.

## Select the task

Inspect remotes, checkout, worktrees and uncommitted changes. Fetch origin and
sync the actual default branch without discarding user work. Isolate changes
when the current checkout cannot safely be updated.

Process the user-selected prompt; otherwise select the next unhandled Markdown
prompt in lexical order. Pair exact basenames using the repository's
`-result.md` or `-results.md` convention. Read result status and linked Issue/PR:
a partial or blocked outbox record does not mean a task is complete. Mention
older unresolved work when relevant without overriding an explicit selection.

If no unhandled prompt exists, report that and stop. Do not invent scope,
Issues, branches or results. Create new inbox prompts only when asked to queue
new work. Publishing a prompt does not execute it or warrant a completion record.

Read the prompt and references. Keep the source immutable; record later user
clarifications in the Issue/result. Reuse the linked Goal/Issue, or create one
for the selected goal. Branch from current default with `codex/` unless an
explicit dependency requires a different base.

## Implement and validate

Stay within the active prompt and explicit user follow-ups. Edit external core
code in its own workspace; record its commit and publication status rather than
copying it into a sidecar. Keep unrelated project configuration separate.

Implement the real application path. Add meaningful unit and integration tests
for changed behavior and failure boundaries. Run required repository checks,
Docker/Compose for runtime changes, and Playwright for browser changes. Separate
offline/mocked, real provider, and signed-in browser evidence. Do not weaken
assertions or production behavior to make tests pass. Report unavailable
prerequisites without claiming validation that did not run.

Use existing ignored environment files through path overrides where appropriate.
Never expose credentials or commit secrets, personal data, local runtime state,
or unrelated changes. Review staged paths and diff before committing.

## Publish and finish

Write the matching outbox with explicit complete/partial/blocked status, source
prompt and Issue, implementation and changed areas, actual validation commands
and outcomes, deployment impact, provider/browser status, external workspace
commits, and exact blockers/follow-ups. Distinguish implementation from verified
behavior. Do not mark the Goal complete while required work remains.

Commit, push and open a PR linked to the Goal and inbox prompt. Include behavior,
changed areas, validation, Docker/Compose and Playwright applicability, provider
status, configuration/deployment impact and skipped checks. Use closing syntax
only when the PR fully satisfies the Goal.

Resolve failures and review findings. Follow existing session authority for
merging without repeating routine permission requests. After required checks
and acceptance pass, merge, clean up only task-owned branches/worktrees, and
safely sync the canonical checkout. Report the PR, commit, outcome and remaining
operator action. Stop after the selected goal unless asked to continue the queue.
Do not schedule a recurring monitor merely because this method is reusable.
