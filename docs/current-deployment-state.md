# Current Deployment State

This snapshot records non-secret deployment state only. Do not add credentials, tokens, private keys, `.env` contents, or admin passwords to this file.

```text
Repository: scottiepowell/cookbook-roadmaps-link
Branch: main
Public hostname: cookbook.roadmaps.link
Base domain: roadmaps.link
AWS region: us-east-2
EC2 instance ID: i-0bdd490b3a71ccddd
App directory: /opt/cookbook
```

## Operator-Reported Control Plane Items

- [x] GitHub variables updated.
- [x] GitHub AWS role secret updated.
- [x] Cloudflare tunnel token secret saved.
- [x] EC2 instance created.

## Still To Verify

- [ ] EC2 instance has SSM-capable instance profile.
- [ ] EC2 appears in Systems Manager Fleet Manager / Managed Nodes.
- [ ] Session Manager shell works.
- [ ] Bootstrap script runs successfully.
- [ ] Preflight script runs successfully.
- [ ] GitHub Actions `status` works.
- [ ] GitHub Actions `start` works.
- [ ] GitHub Actions `deploy` works with `stop_after_deploy=false`.
- [ ] Local Compose verification passes.
- [x] Public Cloudflare route verification passes from the Windows-hosted local
  connector (`/api/health` returned HTTP 200 on 2026-08-29).

## Notes

The repository does not create cloud resources by itself. The currently verified
route uses the Windows-hosted local connector documented in [Local Core
Cloudflare Tunnel](local-core-cloudflare-tunnel.md); EC2 deployment verification
remains separate and still requires the workflow sequence in the [First Deploy
Guide](first-deploy-guide.md).

The public Windows-hosted core currently runs the homepage/login image. Anonymous
`/` returns HTTP 200 and presents login plus first-administrator setup links.
0034N replaced it with `local/vanilla-cookbook-adapter:0034n`, excluded ignored
environment files from the image, and corrected the effective public OIDC
origin. The runtime now loads a dedicated public Google Web client from an
ignored `.env.public` file. Google accepts both its exact public HTTPS callback
and token-client credentials with identity-only scopes; final authenticated
return/session observation is a manual retry.
