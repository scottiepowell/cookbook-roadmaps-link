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
- [ ] Public Cloudflare route verification passes.

## Notes

The repository does not create cloud resources by itself. First deployment still requires operator-controlled AWS, GitHub, and Cloudflare configuration, followed by the workflow sequence in the [First Deploy Guide](first-deploy-guide.md).
