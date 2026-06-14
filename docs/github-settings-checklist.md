# First Deployment Settings Checklist

Use placeholders while reviewing this checklist. Add real values only in the
GitHub and AWS control planes, never in repository files or workflow logs.

## GitHub Actions Secrets

- [ ] `AWS_ROLE_ARN` contains the repository-scoped GitHub OIDC role ARN.
- [ ] `CLOUDFLARE_TUNNEL_TOKEN` contains the token for the Cookbook tunnel.
- [ ] `OPENAI_API_KEY` is configured only if OpenAI features are enabled.
- [ ] `ANTHROPIC_API_KEY` is configured only if Anthropic features are enabled.
- [ ] `GOOGLE_API_KEY` is configured only if Google features are enabled.
- [ ] No static AWS access-key secrets have been created.

## GitHub Actions Variables

- [ ] `AWS_REGION` identifies the EC2 instance region.
- [ ] `EC2_INSTANCE_ID` identifies the Cookbook EC2 instance.
- [ ] `ORIGIN` is the public HTTPS origin for the application.
- [ ] `APP_DIR` identifies the checkout directory on EC2.
- [ ] `DOMAIN` identifies the public Cookbook hostname.
- [ ] `OLLAMA_BASE_URL` is set only when an Ollama endpoint is used.

Use placeholders during setup planning, for example:

```text
AWS_REGION=<AWS_REGION>
EC2_INSTANCE_ID=<EC2_INSTANCE_ID>
ORIGIN=<HTTPS_ORIGIN>
APP_DIR=<APP_DIR>
DOMAIN=<DOMAIN>
OLLAMA_BASE_URL=<OPTIONAL_OLLAMA_URL>
```

## AWS IAM And OIDC Readiness

- [ ] The GitHub OIDC provider exists with audience `sts.amazonaws.com`.
- [ ] The workflow role trust is restricted to
      `scottiepowell/cookbook-roadmaps-link` and branch `main`.
- [ ] The workflow role has only the EC2 and SSM permissions documented in
      `docs/aws-github-oidc-policy.md`.
- [ ] The role ARN is stored in `AWS_ROLE_ARN`, not in repository content.

## EC2 Instance Readiness

- [ ] A current Ubuntu Server instance is running on EBS-backed storage.
- [ ] Its instance profile includes Systems Manager managed-instance access.
- [ ] The SSM Agent is registered and online.
- [ ] Git, Docker Engine, and Docker Compose are installed.
- [ ] `/opt/cookbook` exists and is writable by the chosen runtime user.
- [ ] `scripts/preflight-ec2-runtime.sh` reports no failures.
- [ ] Outbound HTTPS is allowed for AWS, GitHub, image registries, and
      Cloudflare.
- [ ] Inbound HTTP and HTTPS are not open; temporary SSH is restricted to the
      operator's IP and removed after setup.

## Cloudflare Tunnel Readiness

- [ ] A Cloudflare Tunnel exists for this deployment.
- [ ] The public hostname will route the selected domain to `http://app:3000`.
- [ ] The tunnel token is stored only in `CLOUDFLARE_TUNNEL_TOKEN`.
- [ ] DNS and tunnel health can be reviewed in Cloudflare after deployment.
- [ ] The steps in `docs/cloudflare-tunnel-setup.md` have been reviewed.
- [ ] `scripts/verify-local-compose.sh` and
      `scripts/verify-cloudflare-route.sh` are ready for post-deploy checks.

## First Workflow Run Order

- [ ] Run `status` to verify GitHub OIDC and EC2 read permissions.
- [ ] Run `start` and confirm EC2 passes AWS status checks.
- [ ] Confirm the instance is online in Systems Manager.
- [ ] Run `deploy` with `stop_after_deploy` disabled for first-run diagnosis.
- [ ] Verify Docker Compose status and the Cloudflare Tunnel route.
- [ ] Run `restart` once to validate routine SSM operations.
- [ ] Run `stop` when testing is complete to control compute cost.
