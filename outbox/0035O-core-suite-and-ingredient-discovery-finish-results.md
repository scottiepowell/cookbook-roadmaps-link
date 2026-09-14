# 0035O Core Suite and Ingredient Discovery Finish Results

Status: complete. Goal: [Issue #13](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/13).
Source: `inbox/0035O-core-suite-and-ingredient-discovery-finish.md` (unchanged).
Related prior Goal: [Issue #10](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/10).

## Core regression repair

Kept the conversion and parser assertions. Five conversion failures came from
an absent developer SQLite database; the test now loads the shipped ingredient
density CSV into a mocked read boundary. The 750g fixture really contains a raw
CRLF inside quoted JSON-LD; the parser now removes the illegal carriage return
before its existing newline cleanup, preserving nine ingredients and the strict
site regression. The seventh full-suite failure was an auth-gate test inheriting
hosted environment flags; it now isolates and restores those flags while still
asserting that authentication cannot be bypassed. Fork CI exposed five mocked AI
tests that depended on a local key; their test environment now reads stubbed
values at call time. Production key handling and auth gates were not relaxed.

## Discovery delivery

The external core now normalizes accents and `-ies` plurals, recognizes romaine
and iceberg as lettuce for a general lettuce search, keeps specific romaine
searches specific, and prevents a multiword ingredient phrase from matching
across separate ingredient entries. Unit and real SQLite visibility tests cover
ranking and private/public isolation. The sidecar reviewed catalog grew from
three to eight metadata-only, source-attributed HTTPS links. Its maintenance
rule and source list are in `docs/groq-rag-offload.md`. Results still distinguish
all, partial, and no matches, and disclose the bounded 5,000-recipe search.

Core publication: [operator fork PR #1](https://github.com/scottiepowell/vanilla-cookbook/pull/1)
merged at `31816b0`; its fork CI test job passed. The original
`jt196/vanilla-cookbook` grants this account pull but not push, so the fork is
the writable publication path. This PR includes the earlier local Cookbook
customizations required by discovery; no core code was vendored into the
sidecar. The upstream Docker publishing job was intentionally skipped in the
fork; both application images were built locally.

## Validation and runtime

- Full core Vitest suite: 715 passed, 3 existing skipped, 0 failed; repeated
  with `OPENAI_API_KEY` explicitly blank. Fork PR CI: test job passed.
- Sidecar validator: 7 checks passed, including 510 Python tests and 39 offline
  evaluations. New catalog endpoint tests passed.
- Signed-in Playwright against disposable loopback Docker and temporary DB:
  passed for a saved recipe, reviewed public links, partial and no matches.
- Core and sidecar Docker images built as `0035o`; Compose configuration passed.
  Established Git Bash launcher updated the public stack with existing database
  and upload volumes. AI sidecar healthy; local and public core health both
  returned HTTP 200 on 2026-09-14. No private recipes were sent to Groq.

Groq RAG remains disabled: the prior public/generated comparison reduced nano
input 2.2% but increased estimated combined cost 12.2%. The operator chose to
stop pursuing that offload. No new provider validation was needed in 0035O.
The eight-link catalog is reviewed, not a whole-web search; future catalog
growth requires original-page review and URL rechecks.
