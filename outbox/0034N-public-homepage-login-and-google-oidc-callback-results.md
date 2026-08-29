# 0034N Public Homepage Login And Google OIDC Callback Results

Status: implementation complete; final manual authenticated callback observation
is pending an operator login retry.

## Outcome

The previously delivered public homepage and administrator/user separation ADR
are now aligned with mailbox task 0034N. The first public Google OIDC defect was
reproduced safely and corrected.

The public runtime had conflicting origin declarations, with the loopback value
winning inside the process. Its Docker build context also did not exclude the
ignored base `.env` file. The external core now excludes `.env` and `.env.*`
from images, and the replacement public container applies the public HTTPS
origin after the ignored developer environment file.

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

## Boundaries

No Google Drive/storage or unrelated scopes were requested. No production
Save-to-Cookbook, AWS, EC2, GitHub Actions, tunnel route, sidecar identity, role,
session, cookie, or provider-account ownership was added.

