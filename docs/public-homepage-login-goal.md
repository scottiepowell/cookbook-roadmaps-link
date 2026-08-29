# Public Homepage Login Goal

Status: complete and running at `cookbook.roadmaps.link`.

Mailbox task: 0034N.

## Goal

Make `cookbook.roadmaps.link` open on a useful public homepage instead of
defaulting to first-administrator creation. Existing users must have a clear
login path, while the initial setup page remains available as an explicit link
until the first administrator exists.

## Acceptance criteria

- Anonymous `/` requests render the public homepage before and after setup.
- Existing users can reach `/login` from the primary homepage action.
- Before initialization, `/setup` is linked as **Create the first
  administrator** rather than being the default page.
- After initialization, `/setup` keeps its existing fail-closed redirect.
- Public registration appears only when the administrator enables it.
- Authenticated users retain the existing recipe-highlight homepage.
- Admin-only capabilities remain enforced on the server; the homepage does not
  grant or infer administrative authority.
- Homepage-focused tests, Svelte diagnostics, and production build pass before
  the public image is replaced; unrelated full-suite baseline failures are
  recorded without weakening assertions.

## Result

The external core now renders `/` as a public landing page for anonymous users.
The primary action links to `/login`; an uninitialized site also links to
`/setup` as **Create the first administrator**. Once initialized, setup keeps its
existing redirect and registration is shown only when enabled. Authenticated
users retain the recipe-highlight dashboard.

Focused route tests passed (4/4), `svelte-check` reported no diagnostics, the
production Docker build passed, and a private runtime smoke verified `/`,
`/login`, `/setup`, and private-route redirect behavior. The public container
was replaced while retaining its Docker-managed data/upload volumes. External
verification returned HTTP 200 with the landing title and both login/setup
links present.

0034N subsequently corrected the public Google OIDC origin/callback mismatch
without changing the homepage authorization model.

The broader upstream suite reported 661 passes, 3 skips, and 7 unrelated
pre-existing/environment-sensitive failures in recipe parsing/conversion and a
local adapter-route case. No assertions or production behavior were weakened.

## Workspace boundary

The implementation belongs in
`C:\Users\scott\projects\vanilla-cookbook-core`. This sidecar repository owns
the goal, ADR, deployment record, and safe validation evidence. It does not own
users, roles, sessions, or the homepage implementation.
