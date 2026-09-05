# 0034Y Recipe Revision Identity Preservation Results

## Result

Complete and deployed.

Recipe revisions now receive a locked-invariant generation contract and pass a
deterministic identity check before session state is committed. A candidate is
rejected when its directions lose an established dish anchor or it introduces
an unrequested conflicting dish anchor. The existing bounded retry can retry
the safe `revision_identity_drift` category once. A rejected candidate does not
replace the current recipe or consume a successful change.

Intentional substitutions remain supported. Equivalent wording for riced
cauliflower and cauliflower rice is accepted without permitting plain rice to
replace an established pasta dish.

## Safe verification outcomes

- Reported pasta-to-rice/soup regression rejected: yes.
- Rejected revision preserved prior draft: yes.
- Rejected revision preserved revision count: yes.
- Coherent vegetable addition accepted: yes.
- Explicit pasta-to-rice substitution accepted by the guard: yes.
- Live callback to the sidecar returned: yes.
- Live revision completed: yes.
- Live pasta identity remained present: yes.
- Live pasta directions remained present: yes.
- Live unexpected plain-rice directions absent: yes.
- Live unexpected soup directions absent: yes.
- Live successful-change count advanced once: yes.
- Public core remained running: yes.
- Public tunnel remained running: yes.
- Sidecar image: `local/cookbook-ai-sidecar:0034y`.
- Sidecar health: healthy.

No prompt text, generated recipe content, identity data, browser artifact,
credential, token, cookie, session value, environment value, or provider
payload is recorded here.

## Validation

- Repository tests: 434 passed.
- Offline evaluations: 39 passed.
- Focused recipe-session tests: 29 passed.
- Compose configuration: valid with ignored local environment file paths.
- Sidecar image build: passed.
- Public sidecar startup and health: passed.
- `git diff --check`: passed.

The only test warning is the existing Starlette/httpx compatibility deprecation
warning.

## Boundaries retained

No canonical recipe save, authentication ownership, user/session ownership,
public sidecar route, Redis, Protocol Buffers, asynchronous job system, AWS, or
new ingress was added.
