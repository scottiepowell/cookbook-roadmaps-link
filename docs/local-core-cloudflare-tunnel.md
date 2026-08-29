# Local Core Cloudflare Tunnel

Status: running and externally reachable on 2026-08-29.

## Project ownership

`cookbook-roadmaps-link` owns the Cloudflare deployment shape, operational
documentation, AI sidecar, and safe evidence. The separate
`C:\Users\scott\projects\vanilla-cookbook-core` workspace owns the application,
users, sessions, provider links, recipes, and authorization.

## Active local route

The existing remotely managed tunnel configuration required no Cloudflare
dashboard or DNS change. Its public hostname and service target were already:

```text
cookbook.roadmaps.link -> http://app:3000
```

A dedicated Docker network now joins:

```text
Cloudflare connector -> app alias -> public core container:3000
```

The public core uses the existing `local/vanilla-cookbook-adapter:0034l` image,
an ignored environment file, and Docker-managed database/upload volumes. The
app is not published on a host internet-facing port. The connector uses the
existing ignored tunnel token without recording it in repository files or
output.

Safe verification result: `https://cookbook.roadmaps.link/api/health` returned
HTTP 200 with both the core container and tunnel connector running.

## Cloudflare setup

No Cloudflare control-plane change is currently required. If the route is ever
recreated, configure the existing tunnel's public hostname as:

```text
Subdomain: cookbook
Domain: roadmaps.link
Service type: HTTP
Service URL: app:3000
```

Do not point the service at `localhost:3000`; inside the connector container,
that would refer to the connector itself.

## Authentication boundary

This tunnel does not convert the 0034L local Google OIDC path into production
authentication. The 0034L guard intentionally rejects exposed origins. Public
Google login would require a separately reviewed production-auth task, an HTTPS
callback registered with Google, production secret handling, and removal of the
local-only restriction through reviewed core changes. None of that is claimed
or implemented here.
