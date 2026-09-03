# 0034V Transactional AI Recipe Revisions Results

Status: complete and deployed.

## Diagnosis

Safe runtime logs showed three recipe-session message requests returning 503
before a fourth message succeeded. The sidecar committed revised requirements
and incremented the revision before calling the provider, so every failed call
consumed a change. The browser optimistically appended each message and did not
remove it or restore the composer when the request failed.

## Repair

- Stage revised requirements locally and commit them with the new draft only
  after provider generation and schema validation succeed.
- Preserve the existing draft, requirements, and revision on transient failure
  and on budget rejection.
- Return only bounded failure category/retryability metadata to core.
- Retry one transient change request with an identical body through the same
  operator gate and budget guard.
- Remove a failed optimistic message and restore its text to the composer.
- Raise the revision output allowance to 1,800 tokens and the matching total
  token cap to 13,800 while retaining the per-call and per-session cost caps.
- Allow 21 provider attempts: one initial generation plus ten revisions with at
  most one retry each. The user-visible limit remains ten successful changes.

## Validation

- Core `svelte-check`: 0 errors and 0 warnings.
- Core focused Vitest: 10 passed, including one identical bounded retry after a
  retryable 503.
- Sidecar repository validation: 423 tests passed, 39 offline evaluations
  passed, and all 7 repository checks passed.
- Regression coverage proves provider failure and budget rejection retain the
  prior requirements, draft, and revision count.
- The repository validation script now propagates pytest/evaluation failures
  instead of allowing a later successful command to mask them.
- `git diff --check`: passed in both workspaces.
- Public Compose config: passed using ignored environment files without
  displaying their values.
- Images built and deployed: `local/vanilla-cookbook-adapter:0034v` and
  `local/cookbook-ai-sidecar:0034v`.
- Runtime: sidecar healthy, public health 200, no public-app host ports, and the
  independently running tunnel was not recreated.
- Safe funded live nano smoke: initial generation succeeded; one requested
  ingredient change succeeded at revision 1; the requested ingredient was
  present; the model pin was correct; no retry was required. Only booleans and
  counters were recorded.

The external core fix is committed locally on
`openclaw/0034V-transactional-ai-revisions` at
`265b2df2b27a6d44b22138bf3711ec1206e18012`. It was not pushed to the
third-party core remote. The sidecar completion commit records the deployment
configuration, tests, documentation, and mailbox result.
