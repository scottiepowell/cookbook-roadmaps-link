# 0034O Public Authenticated AI Recipe Importer Results

Status: complete and deployed.

## Result

The public Cookbook now offers a core-owned `/ai` recipe-drafting page for
authenticated users. A narrow core proxy delegates only recipe import to the
private FastAPI sidecar and pins the request to `gpt-5.4-nano`. The draft is
review-only and is not saved automatically.

Core owns Google/Lucia authentication, the public page and navigation, the
12,000-character input ceiling, a three-request-per-user/five-minute limit,
safe response shaping, and any future canonical write. The sidecar owns the
OpenAI Responses API call, recipe schema, provider validation, operator gate,
and budget enforcement. No cookie, identity, OAuth artifact, browser
authorization header, canonical database, or uploads mount crosses into the
sidecar.

## Safe deployment evidence

- public health returned 200;
- anonymous `/ai` navigation redirected to login;
- anonymous importer proxy submission returned 401 before the sidecar;
- core reached sidecar health successfully over the private Docker network;
- the sidecar published no host port and received no Cookbook data volume;
- the operator gate allowed only the importer workflow;
- provider/model/live-call/budget preflight passed with budget enforcement;
- one funded synthetic live importer call returned HTTP 200, the expected
  model, a validated draft, three ingredients, four directions, two safe
  warnings, and usage metadata;
- the live call took approximately 7.4 seconds;
- the public Cookbook recovered to HTTP 200 after the preserved known-working
  Cloudflare connector was restored.

The first synthetic request failed closed before provider invocation because
the two sides used different environment variable names for the shared
operator token. The ignored runtime file was corrected to provide both names
with the same generated value, and core and sidecar were recreated. No token
value was printed, persisted outside the ignored runtime file, or committed.

A replacement Cloudflare container also failed closed because a stale
sidecar-repository placeholder was not the working tunnel credential. The new
invalid container was removed and the preserved connector was restored. The
final Compose profile intentionally leaves Cloudflare independently managed;
no DNS or Cloudflare control-plane change was made.

## Validation

- core proxy tests: 3 passed;
- sidecar operator-gate, budget, importer, and provider tests: 45 passed;
- full sidecar repository tests: 410 passed;
- offline AI evals: 39 passed;
- repository validator: all 7 checks passed, including the secret-pattern scan;
- core production image build: passed;
- sidecar production image build: passed;
- public Compose configuration: passed;
- deployed core, private sidecar, and existing tunnel connector: running;
- sidecar health: healthy.

The available browser sessions were signed out, so a final authenticated UI
submission was not fabricated with an exported cookie or synthetic session.
That remains the only manual product check. The core proxy tests verify the
authentication boundary and pinned nano-model forwarding contract, and the
deployed private provider path completed the funded live call.

No secret, token, cookie, OAuth value, raw provider prompt/response, real
recipe input, real profile data, browser artifact, or local environment value
is recorded here.
