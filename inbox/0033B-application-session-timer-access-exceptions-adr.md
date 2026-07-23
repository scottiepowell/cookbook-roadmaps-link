# 0033B Application Session Timer And Access Exceptions ADR

## Goal

Investigate a 30-minute application timer for the Cookbook AI product, including a way to turn the timer off or bypass it for certain users/operators.

This is an ADR/design task only. Do not implement runtime timer enforcement in this task.

## Context

This follows the post-0032A product priority roadmap. The timer is intended as an app-level product/access control concept, separate from AWS platform work.

## Required Work

Create:

```text
docs/application-session-timer-access-exceptions-adr.md
```

The ADR should cover:

- problem statement;
- expected user experience for a 30-minute timer;
- whether the timer should be session-based, route-based, workflow-based, or provider-call-based;
- warning behavior before expiry;
- what happens when time expires;
- how work-in-progress drafts should be handled;
- bypass/exception model for certain users, operators, or invite sessions;
- relationship to existing operator gate, invite sessions, budget enforcement, and provider kill switches;
- privacy/security implications;
- accessibility and user-friendly messaging;
- abuse-prevention considerations;
- implementation options;
- testing strategy;
- explicit non-goals.

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Create:

```text
outbox/0033B-application-session-timer-access-exceptions-adr-results.md
```

## Acceptance Criteria

- ADR exists.
- ADR explains the 30-minute timer concept.
- ADR defines exception/bypass options for selected users/operators.
- ADR does not implement runtime enforcement.
- ADR preserves existing mock/offline validation.
- ADR does not add production auth, payment, analytics, ads, or AWS work.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

## Commit

```bash
git add docs README.md outbox/0033B-application-session-timer-access-exceptions-adr-results.md
git commit -m "docs: add application session timer adr"
git pull --rebase origin main
git push origin main
```
