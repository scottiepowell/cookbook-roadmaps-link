# 0034P Public AI Transient Provider Recovery Results

Status: complete and deployed.

The observed request passed Cookbook authentication and the sidecar operator
gate, then returned a safe 503 after an intermittent provider failure. The
same synthetic dish phrase subsequently returned a validated
`gpt-5.4-nano` draft, confirming that configuration, credits, model routing,
and the recipe request itself were valid.

## Fix

- Sidecar unavailable responses now carry a safe boolean retry decision.
- Timeout, network, temporary provider, invalid/incomplete JSON, and truncated
  structured-output failures allow one bounded retry.
- Account/quota, authentication, model, schema, authorization, payload, and
  rate-limit failures do not retry.
- Core performs at most one retry and sends it through the same private
  sidecar endpoint, operator gate, and provider budget guard.
- If both attempts fail, the UI reports that one bounded retry was used and
  does not expose provider internals.

## Safe verification

- sidecar focused importer tests passed;
- core proxy tests passed, including transient recovery and deterministic
  no-retry coverage;
- full sidecar repository validation passed with 411 tests, 39 offline evals,
  and all 7 repository checks including secret scanning;
- production sidecar and core `0034p` images built successfully;
- the running core and sidecar were replaced without replacing the existing
  Cloudflare connector or Cookbook data volumes;
- public health returned 200;
- the sidecar reported healthy and remained private with no host port;
- one post-deployment live check of the same synthetic dish phrase returned
  HTTP 200, the expected `gpt-5.4-nano` model, a validated draft, 13
  ingredients, and 7 directions in approximately 7 seconds.

No API key, operator token, cookie, OAuth value, user profile, raw provider
prompt/response, or generated recipe content is recorded here.
