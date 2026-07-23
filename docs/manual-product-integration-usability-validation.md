# Manual Product Integration Usability Validation

Status: complete as a mock/offline validation exercise for `0033A`.

This plan validates how the local Cookbook product shell and AI sidecar feel
together. It is a product-usability exercise, not a feature implementation or
a live-provider acceptance run. Normal validation remains mock/offline.

## Scope and startup sequence

1. From the repository root, run `scripts\start-ai-demo-local.ps1 -Provider
   mock`.
2. Confirm `GET /health` is healthy and `GET /demo/readiness` reports
   `mock/mock-basic`, offline mode, generated saved recipes, and local dataset
   availability.
3. Start Docker Compose separately when validating the Vanilla Cookbook
   container. The sidecar `/product/cookbook` link targets the upstream local
   Cookbook at `127.0.0.1:3000`; the sidecar does not rewrite that UI.
4. Open `/product` first, then use `/product/ai` or `/demo` for AI workflows.

The sidecar should expose safe health, readiness, mode, and workflow states.
Provider keys remain server-side. Raw diagnostics are not user-facing. Live
OpenAI remains disabled unless an operator explicitly opts in through the
existing server-side gate.

## Route and workflow walkthrough

`/product` is the starting point. Check that it explains Cookbook and AI as one
product, makes mode/readiness clear, and offers understandable next actions.
`/product/cookbook` hands off to the external Cookbook target and
`/product/ai` hands off to `/demo`; these are current explicit boundaries.

The readiness panel should distinguish service health, saved-recipe
availability, dataset availability, and disabled optional features. Mock mode
must remain deterministic and must not inherit live enablement. Selecting Live
on a mock server should show a controlled unavailable state, with readable
guidance and no provider call.

The manual importer acceptance boundary is separate from this exercise. A live
importer call requires explicit operator approval and exactly one bounded call
per invocation. The observed manual profile is `openai` / `gpt-5.4-nano` at
500 output tokens. It is never part of normal validation.

Walk these workflows and check their input, loading, success, empty, warning,
error, reset, citation, and provenance states:

- Importer: pasted notes produce a schema-validated draft with readable
  warnings and provenance.
- Ask My Cookbook: saved-recipe questions show readable recipe citations and a
  clear missing-data state.
- Dataset Ask: search and questions show bounded results and provenance.
- Meal Planner: preferences produce a plan that explains its saved-recipe
  candidates and unavailable-data recovery.
- Recipe Session: start, clarification, follow-up, requirements/RAG status, and
  demo-only finalize messaging are understandable.

## Usability rubric and gap format

Observe navigation continuity; visual style, spacing, typography, loading and
empty states; natural placement of AI actions; citation readability;
responsive/accessibility behavior; and whether the experience feels like one
product rather than two linked demos.

Record each gap as:

```text
Gap ID:
Area:
Observed behavior:
Expected production behavior:
Severity:
Suggested follow-up task:
Boundary/non-goal:
```

## Current assessment and follow-ups

The mock smoke and UI harness establish that the workflows are reachable,
deterministic, and safely bounded. The product shell is useful as an
operator/demo entry point. It does not establish that the external Cookbook is
running, that production auth/session handoff exists, or that the AI UI is
visually native to the upstream application.

Prioritize follow-up work that removes the visible split: define native
navigation/embedding while preserving the adapter boundary; establish shared
visual, loading, empty, error, focus, responsive, and accessibility contracts;
define safe user/session context handoff; and add a production-shaped
acceptance checklist when both local applications run together. These are
candidates only; this task adds no implementation.

## 0033A execution record

The requested `docs/product-priority-roadmap-after-0032A.md` source file was
absent from this checkout. That limitation is recorded in the outbox and the
requested roadmap update was added. The sidecar ran with `-Provider mock`;
`demo-ai-mock.ps1` passed 39 offline eval cases and endpoint checks; and the
existing local Chromium harness passed 4 tests. The interactive in-app browser
was unavailable, so no screenshot or browser artifact was created. Read-only
route/status checks supplemented the automated results.
