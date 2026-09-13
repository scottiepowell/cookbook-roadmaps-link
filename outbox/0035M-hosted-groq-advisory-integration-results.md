# 0035M Hosted Groq Advisory Integration Results

Source: [0035M inbox](../inbox/0035M-hosted-groq-advisory-integration.md)

Goal: [Issue #8](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/8)

## Delivered

The sidecar has a dedicated hosted Groq Chat Completions adapter, strict JSON
Schema and local source-ID/quantity checks, one transient retry, a short
circuit breaker, budget metering, aggregate-only logs, and a deterministic
fallback. The nine native Kitchen ideas tasks and their remaining scope are
documented in the [pilot guide](../docs/groq-advisory-pilot.md). Existing
OpenAI `gpt-5.4-nano` final recipe output and core save authority remain.

The external core workspace owns the authenticated API proxy and Add a recipe
page panel. Its local `codex/groq-advisory-ui` commit is `1204f59`. The
upstream `jt196/vanilla-cookbook` remote grants this account read-only access,
so that core commit is local and the corresponding Docker image is local. No
core source was copied into this sidecar repository.

The public Compose stack now accepts explicit paths to the canonical ignored
sidecar environment and dataset when launched from a worktree. The existing
ignored `.env` supplied the key at runtime; only its non-secret Groq heading
needed a comment marker for Compose parsing. No secret value was printed,
committed, or added to core configuration.

## Validation

- Sidecar Git Bash validator: 496 Python tests, 39 offline evaluations, and
  seven repository checks passed.
- Core focused tests: 22 tests across advisory proxy, existing recipe chat,
  and AI-first entry passed. Production core Docker build passed.
- Core broad suite: 695 passed, three skipped, seven failures in existing
  importer auth, ingredient conversion, and external recipe parsing tests.
  The failing files were outside this change; assertions were not altered.
- Generated-fixture Groq smoke: all nine task contracts passed live, with
  2,606 input and 1,566 output tokens on the final run.
- Public Docker: core `0035m` running, sidecar `0035m` healthy, local core
  health HTTP 200, public health HTTP 200. A request from the running core
  container to the running sidecar returned HTTP 200, `provider=groq`, one
  item, and token usage for a generated `carrots` shopping fixture.
- Browser: the public `/ai` route redirected an unsigned browser to the
  Cookbook login page, as expected. A signed-in interactive UI check could
  not be completed in that browser session; the app remains running for the
  operator's login and Kitchen ideas test.

## Limits and next test

Groq account zero-data-retention state was not verified. The pilot requires
an explicit public/invented-data confirmation and rejects obvious sensitive
input; private saved recipes and transcripts are not routed to Groq. Free
quota has no production capacity guarantee. The native Kitchen ideas tasks
are standalone advisory turns; population-level token savings versus the
baseline have not been measured.

Sign in at `https://cookbook.roadmaps.link`, open **Add a recipe**, expand
**Kitchen ideas**, choose **Shopping aisle labels**, enter `carrots`, confirm
public/invented text, and select **Get ideas**. No suggestion is saved.
