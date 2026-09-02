# 0034O — Public Authenticated AI Recipe Importer

## Goal

Connect the existing FastAPI AI sidecar to the public Cookbook experience as a
small authenticated feature slice. Returning Cookbook users can paste recipe
text and receive a reviewable OpenAI draft generated with `gpt-5.4-nano`.

## Ownership

- Vanilla Cookbook core owns the page, navigation, Google/Lucia session check,
  request size/rate limits, public response, and any future canonical save.
- The sidecar owns the provider abstraction, recipe-draft schema, prompt,
  OpenAI Responses API call, output validation, and provider-budget guard.
- Cloudflare continues to route only to core at `app:3000`; the sidecar has no
  public hostname or host port.

## Required work

In the external core workspace:

- add an authenticated `/ai` recipe-drafting page;
- add one authenticated proxy endpoint for sidecar recipe import;
- pin the proxy request to `openai/gpt-5.4-nano`;
- enforce a 12,000-character payload ceiling and a per-user request limit;
- keep the internal sidecar token server-side;
- return only a reviewable draft, safe warnings, and safe unavailable states;
- add the AI page to authenticated desktop/mobile navigation;
- do not save or mutate a recipe automatically.

In this repository:

- add a repeatable public Compose topology with core and private sidecar on the
  existing connector's Docker network, without replacing its token/runtime;
- require an ignored shared proxy token and the existing ignored OpenAI key;
- enable only the importer workflow at the sidecar operator gate;
- retain provider call, token, per-call, per-session, and cost caps;
- update public-route, runtime, status, backlog, and acceptance documentation;
- record only safe live verification outcomes.

## Safety boundaries

Do not expose `/demo`, `/ai/config`, `/ai/admin/*`, `/ai/invite/*`,
`/ai/recipe-session/*`, `/dataset/*`, `/recipes/search`, meal planning, or Ask
My Cookbook. The sidecar must not receive core cookies, Google/OIDC artifacts,
user identity, or authorization headers. It must not mount the canonical
Cookbook database or uploads.

Do not print, commit, or persist API keys, proxy tokens, cookies, sessions,
OAuth values, raw provider prompts/responses, real recipe text, or profile data.
Do not add Drive/storage scopes, production Save-to-Cookbook, AWS, payment,
analytics, ads, or sidecar identity/session ownership.

## Acceptance criteria

- Anonymous `/ai` redirects to `/login`.
- Anonymous proxy calls return 401 without contacting the sidecar.
- Authenticated proxy calls are pinned to `gpt-5.4-nano`.
- The browser never receives the sidecar token or OpenAI key.
- Oversized and over-rate requests are blocked before provider invocation.
- Sidecar is reachable from core but has no host/public port.
- Sidecar gate allows only importer and budget mode is enforced.
- One synthetic funded nano call succeeds through the deployed core proxy.
- Public Cookbook and Google login remain available.
- Repository/core validation, Compose validation, and whitespace checks pass.

## Validation

Normal tests remain mock/offline. Exactly one minimal live call is allowed only
after configuration, auth, network, model, gate, and budget preflight pass.
