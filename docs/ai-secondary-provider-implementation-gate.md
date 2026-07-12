# AI Secondary Provider Implementation Gate

## Purpose

This document defines the implementation gate that must pass before any future secondary/offload provider runtime adapter task can start.

This is a docs-first gate only. It does not implement provider runtime behavior.

## Current Status

- Current candidate in scope: `GLM-4.7 Flash`
- Current implementation status: not implemented
- Current gate decision: `blocked`
- Current reason: primary provider documentation was not available in this task

## Gate Requirements

No future runtime adapter task may start until all of these are satisfied:

- all required facts verified from primary documentation
- source references recorded
- privacy/data-use terms acceptable for intended inputs
- private user recipe data blocked unless a future privacy decision allows it
- allowed task classes match the `0031A` ADR
- blocked task classes remain blocked
- fallback returns to primary baseline
- budget and usage reporting semantics are defined
- operator/invite controls are respected where applicable
- normal validation remains offline
- secondary output cannot become final user-visible answer without primary validation
- offline evals prove bad secondary output is ignored
- runtime adapter work requires a separate future mailbox task

## Go / No-Go Matrix

| Gate area | Required state | Current GLM-4.7 Flash status | Decision |
| --- | --- | --- | --- |
| Primary documentation references | Recorded and reviewable | `unverified` | `no-go` |
| API protocol and auth | Verified from primary docs | `unverified` | `no-go` |
| Pricing | Verified from primary docs | `unverified` | `no-go` |
| Privacy / retention / training terms | Verified and acceptable | `unverified` | `no-go` |
| Context / token limits | Verified from primary docs | `unverified` | `no-go` |
| Error shape / timeout / retry guidance | Verified from primary docs | `unverified` | `no-go` |
| Allowed offload tasks | Match `0031A` only | `candidate policy only` | `partial` |
| Blocked task classes | Still blocked | `yes` | `go` |
| Final-answer path | Still OpenAI `gpt-5.4-nano` | `yes` | `go` |
| Fallback behavior | Returns safely to the primary baseline | `ADR-defined only` | `partial` |
| Budget / reporting semantics | Defined for future runtime integration | `not implemented` | `no-go` |
| Operator / invite controls | Preserved where applicable | `not implemented` | `no-go` |
| Offline validation | Remains default | `yes` | `go` |
| Separate future mailbox task | Required | `not started` | `go` |

## Implementation Gate Decision Rules

### Go

Mark the implementation gate `go` only when:

- every required fact category in [AI Secondary Provider Fact Register](ai-secondary-provider-fact-register.md) is verified from primary documentation;
- source references are recorded for those facts;
- privacy, retention, training-use, and account/billing requirements are accepted for the intended input boundary;
- allowed task classes are still limited to the bounded advisory classes from `0031A`;
- final-answer generation remains on the primary baseline unless a later separate decision changes that;
- offline evals prove unsafe or low-quality secondary output is ignored cleanly;
- a separate mailbox task is explicitly approved for runtime adapter work.

### No-Go

Keep the gate `blocked` when any of the following is true:

- any required fact remains `unknown`, `unverified`, or `not approved`;
- pricing is missing;
- privacy or retention policy is missing;
- private user recipe data would cross the boundary without a separate privacy decision;
- final-answer generation is proposed for the secondary provider;
- blocked task classes are weakened or removed;
- fallback behavior is missing;
- runtime work is proposed without a separate mailbox task.

## Required Runtime Boundary If A Later Task Starts

Even after the gate passes, a future runtime adapter task must still preserve these boundaries:

- the current OpenAI `gpt-5.4-nano` path remains the final-answer baseline unless a later separate decision changes it;
- the corrected 0030 baseline, including the `0030P` no-bake cheesecake clarification behavior, remains part of the regression floor;
- operator gate, invite sessions, budget guard, usage reporting, route exposure review, and monetization boundary controls remain in force;
- normal validation stays offline and mock-only;
- live provider checks remain explicit opt-in only.

## Separate Task Requirement

Passing this gate does not authorize direct implementation.

Any runtime adapter work still requires:

1. a new future mailbox task;
2. an explicit request-routing design;
3. bounded payload definitions;
4. budget and reporting integration details;
5. offline and opt-in live validation requirements.

## Non-Goals

- No runtime GLM support
- No secondary-provider routing
- No automatic fallback
- No live GLM calls
- No SDK dependencies
- No production behavior changes
