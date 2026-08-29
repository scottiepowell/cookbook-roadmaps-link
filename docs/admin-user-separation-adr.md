# ADR: Administrator And User Separation

Status: accepted.

Mailbox task: 0034N.

## Context

The first public Cookbook request previously redirected directly to `/setup`,
which made administrator bootstrap look like the normal user entry point. The
application already stores `isAdmin` and `isRoot` on core-owned AuthUser records
and protects administrative routes server-side, but the public journey did not
explain the distinction.

## Decision

Vanilla Cookbook core remains the sole owner of identities, sessions, and roles.
Administrators and ordinary users share the same authentication system and login
page; authorization is separated after authentication.

The public homepage exposes distinct actions:

1. **Log in to your cookbook** is the primary action for every existing user,
   including administrators.
2. **Create the first administrator** links to `/setup` only while the database
   is uninitialized.
3. **Create an account** appears only after initialization and only when the
   administrator has enabled registration.

The initial setup path creates the first root administrator. Normal registration
and OIDC auto-provisioning create ordinary users without administrative rights.
Role promotion/demotion remains an authenticated admin operation, enforced by
core server routes. Existing last-admin and root-account protections remain in
force.

## Authorization rules

- Authentication answers who the caller is; `isAdmin`/`isRoot` authorization
  answers what the caller may do.
- Homepage visibility never grants a role.
- Anonymous users cannot reach private recipe or admin routes.
- Ordinary users own their recipes and settings and cannot manage other users or
  site configuration.
- Administrators may manage site/user configuration only through protected core
  routes.
- The sidecar, Cloudflare connector, and AI API do not assign roles or own
  sessions.

## Consequences

The public entry point is understandable for returning users without weakening
initial bootstrap. Administrator creation is deliberate rather than automatic,
and registration policy stays under administrator control. 0034N separately
approved the public Google identity-only callback; that does not change this
role model, grant administrative authority, add storage scopes, or move token
and session custody outside the core.
