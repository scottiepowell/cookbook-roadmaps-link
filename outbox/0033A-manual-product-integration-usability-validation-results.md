# 0033A Manual Product Integration Usability Validation Results

## Summary

- Validation plan created at [manual product integration usability validation](../docs/manual-product-integration-usability-validation.md).
- Mock/offline local sidecar started through `start-ai-demo-local.ps1 -Provider mock`.
- The requested roadmap source file was missing; it was added at
  `docs/product-priority-roadmap-after-0032A.md` and the limitation is recorded
  in the validation note.

## Checks performed

- `GET /health` passed.
- `GET /demo/readiness` reported `mock/mock-basic`, offline mode, generated
  saved recipes, and local dataset availability.
- `scripts/demo-ai-mock.ps1` passed 39 offline eval cases and endpoint smoke
  checks for importer, Ask My Cookbook, Dataset Ask, Meal Planner, and Recipe
  Session.
- `scripts/run-ui-playwright.ps1` passed 4 deterministic Chromium tests,
  including mock mode propagation and safe live-unavailable behavior.
- Read-only route checks confirmed `/product` is available, `/product/cookbook`
  redirects to the external local Cookbook target, and `/product/ai` redirects
  to `/demo`.
- The in-app interactive browser was unavailable in this environment, so full
  manual visual inspection could not be completed. No screenshots, traces, or
  browser artifacts were created or committed.

## Product integration observations

The product shell is a useful local/demo entry point: it explains the two
surfaces, exposes readiness, and links to the workflow workspace. Mock behavior
is deterministic and the workflow smoke is broad. The main usability concern is
that the current experience still communicates a handoff between an upstream
Cookbook container and a separate AI demo workspace rather than a single
native product.

## Top usability gaps and follow-ups

| Gap ID | Area | Observed behavior | Expected production behavior | Severity | Suggested follow-up task | Boundary/non-goal |
| --- | --- | --- | --- | --- | --- | --- |
| 0033A-UX-01 | Navigation | Cookbook and AI are separate handoffs; AI opens `/demo`. | Shared navigation preserves context and makes AI actions feel native to Cookbook. | High | Define native navigation/embedding handoff through the adapter contract. | No route rewrite or auth in this task. |
| 0033A-UX-02 | Visual continuity | Product shell and workflow workspace are separate sidecar surfaces. | Shared visual tokens, spacing, typography, loading, empty, and error states. | High | Create an integrated UI contract and implementation task. | Do not rewrite upstream Vanilla Cookbook here. |
| 0033A-UX-03 | Runtime handoff | Cookbook target depends on a separate local container at port 3000. | Integrated acceptance proves both apps are available and explains recovery clearly. | Medium | Add a production-shaped two-app acceptance checklist. | No Docker/platform change here. |
| 0033A-UX-04 | Manual inspection | Interactive browser was unavailable for this run. | Repeat responsive/accessibility/manual visual review in an environment with a browser. | Medium | Schedule a follow-up manual QA run. | No screenshots or browser artifacts committed. |

## Recommended follow-up tasks

1. Native navigation and shared-context design for Cookbook-to-AI handoff.
2. Shared UI state/accessibility contract for integrated AI panels.
3. Safe user/session context handoff design that preserves recipe scope.
4. Two-container local acceptance runbook once Vanilla Cookbook is available.

## Explicit non-goals

No new features, AWS/platform/IaC work, SSO, BYOS, analytics, ads,
monetization, payment, production auth, live OpenAI calls, provider routing,
database writes, UI rewrite, screenshots, traces, prompts, provider outputs,
raw datasets, generated indexes, secrets, or local environment values were
added.
