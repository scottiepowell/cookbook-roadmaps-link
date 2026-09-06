# 0035A Public AI Retry Visibility and Compound Edits Results

## Result

Complete and deployed.

Core permits up to three bounded automatic retries for retryable transport and
explicitly transient sidecar failures. Four total attempts share a 90-second
deadline, and retries preserve the initial request body and opaque idempotency
key. Deterministic failures remain no-retry.

The browser now displays the latest request's retry use directly below the
successful-change counter, including `0 of 3 bounded retries used`. Safe retry
metadata is also returned after exhausted requests while the prior draft and
change count remain intact.

Additive ingredient plus serving prompts are classified as relevant changes to
the current draft. Existing numeric ingredient quantities are scaled
deterministically, provider-added ingredients are retained, the exact yield is
set, and the revision commits only if every recognized requested addition is
present. Potato wording, including the reported apostrophe form, is tracked.

## Safe verification outcomes

- Initial clarification behavior retained: yes.
- Relevant existing-draft changes avoid initial vague-idea clarification: yes.
- Additive and serving intent handled in one prompt: yes.
- Requested ingredient required before commit: yes.
- Exact doubled yield enforced: yes.
- Existing numeric ingredient quantities scaled consistently: yes.
- Failed revisions remain transactional: yes.
- Maximum bounded retries: 3.
- Maximum total attempts per request: 4.
- Identical retry body: yes.
- Identical initial idempotency key: yes.
- Non-retryable failure stops immediately: yes.
- Zero retry count displayed: yes.
- Fourth-attempt recovery covered: yes.
- Public compound change committed once: yes.
- Public exact doubled yield observed: yes.
- Public requested ingredient observed: yes.
- Public latest-request retry count observed: yes.
- Public health: 200.
- Public core image: `local/vanilla-cookbook-adapter:0035a`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035a`.
- Sidecar health: healthy.
- Cloudflare tunnel remained running: yes.

No prompt text, generated recipe content, provider payload, identity data,
browser artifact, credential, token, cookie, session value, or environment
value is recorded here.

## Validation

- Repository validator: passed all 7 checks.
- Sidecar tests: 460 passed.
- Offline evaluations: 39 passed.
- Focused core recipe-chat tests: 8 passed.
- Core production build: passed.
- Core image build: passed.
- Sidecar image build: passed.
- Public Compose configuration: valid.
- Public container startup and health: passed.
- Filtered startup failure scan: no obvious failures.
- `git diff --check`: passed.

The upstream core's full test suite reported 675 passed, 3 skipped, and 7
unrelated existing failures in legacy recipe parsing, ingredient conversion,
and a local adapter authentication fixture. The focused AI proxy suite and
production build pass; no unrelated assertions or production behavior were
changed. Existing build warnings about Browserslist age, CSS `@property`, and
SvelteKit/Svelte exports remain unchanged.

## Delivery

The external Vanilla Cookbook core change is committed locally on
`openclaw/0035A-retry-visibility-compound-edits` at
`d5d72a392e22f9aac2ca32df1979a1b06ca282c5`. It is not pushed to the upstream
third-party repository.

The mailbox, sidecar, Compose, tests, and project documentation are committed
and pushed in `scottiepowell/cookbook-roadmaps-link`.

## Boundaries retained

No canonical recipe save, authentication/session ownership change, public
sidecar route, Redis, Protocol Buffers, asynchronous job system, AWS, or new
ingress was added.
