# 0034N Public Homepage Login And Google OIDC Callback Results

Status: both local runtime defects are corrected; final operator account
selection and authenticated callback observation are pending.

## Outcome

The previously delivered public homepage and administrator/user separation ADR
are now aligned with mailbox task 0034N. The first public Google OIDC defect was
reproduced safely and corrected.

The public runtime had conflicting origin declarations, with the loopback value
winning inside the process. Its Docker build context also did not exclude the
ignored base `.env` file. The external core now excludes `.env` and `.env.*`
from images, and the replacement public container applies the public HTTPS
origin after the ignored developer environment file.

Continued investigation found a second independent defect: the shared
local-development client-secret value loaded by the public container was not a
valid Google client secret. Google rejected that credential at the token
endpoint with the safe `invalid_client` category. Public authentication now uses
a dedicated Google Web application client and an ignored `.env.public` runtime
file, leaving the loopback development client unchanged.

## Safe verification

- Public homepage returned HTTP 200.
- The public container and Cloudflare connector were running.
- The effective runtime origin was the public HTTPS hostname.
- The OIDC authorization request returned a Google redirect.
- The callback was exactly the public HTTPS core callback, not loopback.
- Scopes were exactly `openid email profile`.
- State, PKCE, and nonce were present.
- The exact public callback was added to the existing Google Web application
  OAuth client.
- Google accepted the authorization request without a redirect URI mismatch and
  returned its login surface.
- An operator screenshot captured an earlier public-callback request that Google
  rejected with a redirect URI mismatch; the app then returned safely to its
  public login page with a generic OIDC failure.
- A refreshed provider-client inspection confirmed both the loopback development
  callback and the exact public HTTPS callback are saved.
- New desktop and Android-style requests generated after that confirmation both
  reached the Google login surface without redirect mismatch.
- The dedicated public client contains only the public HTTPS JavaScript origin
  and exact public HTTPS callback.
- The replacement credential was checked with a deliberately invalid OAuth code;
  Google's `invalid_grant` response proved that the client ID/secret pair itself
  was accepted without completing or recording an authentication.
- A signed-in-browser authorization probe reached Google account selection with
  no redirect mismatch or invalid-request response. No account was selected.
- The first generated public secret became visible during provider-console
  inspection and was disabled before deployment. The replacement secret was
  transferred directly into the ignored runtime file without emitting or
  committing its value.
- The core image contained no ignored `.env` file.
- Existing Docker-managed database and upload volumes were retained.

No client identifier, secret, OAuth code, token, cookie, session value, state,
PKCE value, nonce value, real profile data, browser state, environment value,
database content, or upload was recorded or committed.

## Remaining manual observation

Account selection and the final authenticated return through the corrected
public callback were not automated. The operator should retry **Log in with
Google** from `https://cookbook.roadmaps.link/login` and report only whether the
browser returns to the public hostname and the core accepts the session.

This retry is entirely public and does not require access to the Windows host.
It must begin from the Cookbook login page so the core generates a new state,
PKCE challenge, nonce, and authorization request with the dedicated public
client.
The safe completion signal is exactly two booleans: public-hostname return
succeeded and authenticated core session succeeded. No account name, email,
profile, cookie, token, code, state, or session value is needed.

## Boundaries

No Google Drive/storage or unrelated scopes were requested. No production
Save-to-Cookbook, AWS, EC2, GitHub Actions, tunnel route, sidecar identity, role,
session, cookie, or provider-account ownership was added.
