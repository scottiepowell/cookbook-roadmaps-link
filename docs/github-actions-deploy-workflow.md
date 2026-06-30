# GitHub Actions EC2 Control And Deployment

The manual `Cookbook EC2 Control` workflow controls one EC2 instance and
deploys Vanilla Cookbook without SSH. GitHub Actions obtains short-lived AWS
credentials through OIDC, and AWS Systems Manager Run Command executes remote
deployment operations.

Before the first run, prepare and validate the host with
`docs/ec2-runtime-bootstrap.md`, then complete
`docs/github-settings-checklist.md`.

## GitHub Settings

Configure these GitHub Actions secrets:

```text
AWS_ROLE_ARN
CLOUDFLARE_TUNNEL_TOKEN
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

`AWS_ROLE_ARN` is required for every action. `CLOUDFLARE_TUNNEL_TOKEN` is
required for deployment. The three LLM API keys are optional and may remain
unset. Never use repository variables for these values.

Configure these GitHub Actions variables:

```text
AWS_REGION
EC2_INSTANCE_ID
ORIGIN
APP_DIR
DOMAIN
OLLAMA_BASE_URL
```

Recommended values:

```text
ORIGIN=https://cookbook.roadmaps.link
APP_DIR=/opt/cookbook
DOMAIN=cookbook.roadmaps.link
```

`OLLAMA_BASE_URL` is optional. The workflow defaults an unset `APP_DIR` to
`/opt/cookbook`; set it explicitly for clearer configuration.

## AWS And EC2 Requirements

- Configure the repository-specific OIDC role described in
  `docs/aws-github-oidc-policy.md`.
- Attach an instance profile with Systems Manager permissions, such as
  `AmazonSSMManagedInstanceCore`, to the EC2 instance.
- Install and run the SSM agent.
- Install Git, Docker Engine, and the Docker Compose plugin.
- Allow outbound HTTPS access for AWS Systems Manager, GitHub, Docker image
  pulls, and Cloudflare Tunnel.
- Ensure SSM Run Command can write to `APP_DIR` and invoke Docker. No inbound
  SSH, HTTP, or HTTPS rule is required by this workflow.

## Cloudflare Requirements

Create a Cloudflare Tunnel and configure its public hostname
`cookbook.roadmaps.link` to route to `http://app:3000` on the Compose network.
Store the tunnel token only in the `CLOUDFLARE_TUNNEL_TOKEN` GitHub secret.
See `docs/cloudflare-tunnel-setup.md` for the dashboard, DNS, validation, and
troubleshooting runbook.

Follow `docs/operations-runbook.md` for the full day-2 sequence and
`docs/backup-restore.md` before upgrades or data recovery.

## Running The Workflow

Open the repository's **Actions** tab, select **Cookbook EC2 Control**, choose
**Run workflow**, and select an action:

- `status`: show the current EC2 state and private IP without changing it.
- `start`: start the instance if needed, then wait for EC2 status checks.
- `deploy`: start and validate the instance, wait for SSM, clone or update the
  repository in `APP_DIR`, atomically render `.env`, and run `deploy.sh`.
- `restart`: start and validate the instance, wait for SSM, then restart the
  existing Docker Compose services without updating code or `.env`.
- `stop`: stop the instance and wait until AWS reports it stopped.

Select `stop_after_deploy` to stop EC2 after a successful `deploy`. It does not
alter the behavior of the other actions. A failed deployment leaves the
instance running for diagnosis.

## Cost Control

Use `stop` when the lab is idle, or enable `stop_after_deploy` for a deployment
that only needs to validate startup. Stopping EC2 ends compute charges but does
not remove EBS, Elastic IP, Cloudflare, or other service charges. A stopped app
and tunnel are unavailable at the custom domain.

## Secret Safety

The workflow does not use `set -x`, print `.env`, or echo secret values. It
builds the environment payload in memory and writes `.env` remotely with mode
`0600`. SSM command access is privileged: restrict IAM access to command
details and history because the deployment command carries the encoded
environment payload needed to construct `.env`.

Review workflow changes before running a deployment. Do not print generated
SSM parameter files, shell environment variables, GitHub contexts, or the
remote `.env` during troubleshooting.

## Troubleshooting SSM Shell Errors

If SSM output shows `set: Illegal option -o pipefail`, the remote payload ran
under `/bin/sh` instead of Bash. The deploy and restart workflow actions wrap
their remote payloads with `bash -lc` before sending them to
`AWS-RunShellScript`, so Bash-only options and conditionals are interpreted by
Bash on the instance.
