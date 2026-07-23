# 0030I-8U bounded live importer 1000-token cap profile results

Added an explicit `-MaxOutputTokens` parameter to the approval-gated live
importer diagnostic. The default behavior remains the configured 300-token
profile; the diagnostic-only override accepts values through 1000 and safely
rejects values above 1000. Every safe envelope reports
`requested_max_output_tokens`, including preflight, blocked, success, and
failure results.

Safety boundaries remain unchanged: `-PreflightOnly` never calls the provider,
`-ApproveLiveCall` is required, the model remains `gpt-5.4-nano`, budget checks
remain active, one importer call is permitted per invocation, automatic
retries are absent, and raw provider output and secrets are not emitted.

The prior 300-token live diagnostic still failed as
`output_cap_or_incomplete_response` with `JSONDecodeError`. The 1000-token
profile is an explicit manual diagnostic only; normal validation remains
mock/offline. If a later approved 1000-token run succeeds, operators should
dial down manually: `1000 -> 800 -> 600 -> 500 -> 400 -> 300`.

No live OpenAI call was made for this task. AWS/platform work was not started.
