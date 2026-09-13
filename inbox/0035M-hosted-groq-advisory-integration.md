# 0035M Hosted Groq Advisory Integration

## Source

The operator requested implementation of the hosted Groq offload described in
`0033G`, including applicable advisory candidates, and asked for the next touch
point to be a browser-test-ready integrated Cookbook. This follow-on request
also requires preserving the inbox/outbox GitOps delivery process.

## Goal

Implement a separate server-side Groq adapter with strict bounded contracts,
failure fallback, metering, safe secret loading, and offline tests. Expose useful
advisory cooking tasks in the native Cookbook browser flow. Keep canonical
recipe generation and save under existing OpenAI/core authority. Use only public
or generated payloads until account privacy controls are verified. Validate the
public Docker route and write a matching safe result record.

## Boundaries

The sidecar repository owns the adapter, deployment, documentation, tests, and
result record. The external core owns its authenticated UI and API proxy.
Secrets and runtime data stay ignored. Concessions is unrelated.
