# Cookbook project boundary

This repository is the `cookbook-roadmaps-link` sidecar and delivery repository.
It owns mailbox tasks, architecture and operations documentation, deployment
assets, the AI API/sidecar, evaluations, and safe result records.

It does **not** own Vanilla Cookbook users, sessions, provider-account links,
canonical recipes, or the core application UI. Those belong to the separate
external workspace:

```text
C:\Users\scott\projects\vanilla-cookbook-core
```

Use the external core workspace for Vanilla Cookbook application and OIDC code.
Do not copy or vendor that source into this repository. Keep secrets and local
runtime data ignored. Record only safe, non-secret outcomes here.

For the public route, this repository owns the Cloudflare deployment/runbook
shape. The expected route is `cookbook.roadmaps.link` to `http://app:3000` on a
shared Docker network. The core workspace supplies the app image; Cloudflare
Tunnel supplies public ingress.
