# Task 0003: Create GitHub Actions EC2 control and deploy workflow

## Goal

Create the first GitHub Actions workflow for controlling the AWS EC2 runtime VM and deploying Vanilla Cookbook through AWS Systems Manager Run Command.

The workflow should be manual-only and support these actions:

- `status`
- `start`
- `deploy`
- `restart`
- `stop`

This task should create workflow and documentation files only. Do not configure real AWS, Cloudflare, OpenAI, or GitHub secrets.

## Project context

This repo deploys Vanilla Cookbook to:

https://cookbook.roadmap.links

The stack uses:

- GitHub Actions as the deployment and secrets-management control plane.
- AWS EC2 as the runtime VM.
- Docker Compose for Vanilla Cookbook and Cloudflare Tunnel.
- AWS Systems Manager Run Command for remote commands.
- AWS OIDC for GitHub Actions authentication.

Task 0002 already created the runtime scaffold: `docker-compose.yml`, `.env.example`, `.gitignore`, `deploy.sh`, and `docs/runtime-scaffold.md`.

## Important rules

- Do not commit secrets.
- Do not print secrets in workflow logs.
- Do not create fake credentials.
- Do not use static AWS access keys.
- Use GitHub Actions OIDC with `aws-actions/configure-aws-credentials@v4`.
- Use GitHub Actions secrets for sensitive values.
- Use GitHub Actions variables for non-sensitive deployment configuration.
- Use AWS Systems Manager Run Command instead of SSH.
- Keep the workflow manual-only for now using `workflow_dispatch`.
- The workflow should be safe to review before anyone adds real secrets.

## Required GitHub settings model

GitHub Actions secrets:

```text
AWS_ROLE_ARN
CLOUDFLARE_TUNNEL_TOKEN
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

Only `AWS_ROLE_ARN` and `CLOUDFLARE_TUNNEL_TOKEN` should be required for the base deployment. LLM-related keys should be optional.

GitHub Actions variables:

```text
AWS_REGION
EC2_INSTANCE_ID
ORIGIN
APP_DIR
DOMAIN
OLLAMA_BASE_URL
```

Use these expected default values in documentation only:

```text
ORIGIN=https://cookbook.roadmap.links
APP_DIR=/opt/cookbook
DOMAIN=cookbook.roadmap.links
```

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
find . -maxdepth 4 -type f | sort
```

Record key findings in the outbox report.

### 2. Create `.github/workflows/cookbook-ec2-control.yml`

Create a manual workflow named `Cookbook EC2 Control`.

The workflow should:

- Use `workflow_dispatch`.
- Provide an `action` input with choices: `status`, `start`, `deploy`, `restart`, and `stop`.
- Provide a `stop_after_deploy` boolean input with default `false`.
- Use minimal permissions: `id-token: write` and `contents: read`.
- Use `aws-actions/configure-aws-credentials@v4` with the GitHub secret `AWS_ROLE_ARN` and variable `AWS_REGION`.
- Use the repository variable `EC2_INSTANCE_ID` as the target instance.

### 3. Implement EC2 control behavior

The workflow should include steps to:

- Validate required settings.
- Check EC2 status when action is `status`.
- Start EC2 when action is `start`, `deploy`, or `restart`.
- Wait for the instance to be running and pass status checks.
- Stop EC2 when action is `stop` or when `stop_after_deploy` is true.

Use AWS CLI EC2 commands for start, stop, describe, and wait operations.

### 4. Implement deploy through SSM

The deploy path should use AWS Systems Manager Run Command with the `AWS-RunShellScript` document.

The remote deployment should:

- Ensure the app directory exists, defaulting to `/opt/cookbook`.
- Ensure the repository exists or can be updated there.
- Render the runtime `.env` from GitHub Actions secrets and variables without printing secret values.
- Run the existing `deploy.sh` script.
- Return useful SSM command status and output.

Keep the implementation simple and readable. Avoid `set -x`. Do not print the `.env` file contents.

### 5. Create AWS OIDC documentation

Create:

```text
docs/aws-github-oidc-policy.md
```

Document the IAM role setup needed for GitHub Actions OIDC.

Include:

- High-level OIDC trust relationship explanation.
- Minimum permission areas needed.
- Example IAM permissions policy for this repo.
- Warning to scope trust to this specific repo and branch.
- Reminder that the EC2 instance itself also needs an instance profile with Systems Manager permissions, such as `AmazonSSMManagedInstanceCore`.

Do not include real account IDs. Use placeholders such as `ACCOUNT_ID`, `scottiepowell/cookbook-roadmaps-link`, and `main`.

The permissions policy should cover only what this workflow needs:

```text
ec2:StartInstances
ec2:StopInstances
ec2:DescribeInstances
ssm:SendCommand
ssm:GetCommandInvocation
ssm:ListCommandInvocations
ssm:DescribeInstanceInformation
```

If additional permissions are needed, document why.

### 6. Create deployment workflow documentation

Create:

```text
docs/github-actions-deploy-workflow.md
```

Document:

- What the workflow does.
- Required GitHub secrets.
- Required GitHub variables.
- Required AWS EC2 setup.
- Required Cloudflare setup.
- How to run `status`, `start`, `deploy`, `restart`, and `stop`.
- Cost-control notes about stopping EC2 when not in use.
- Safety notes about not logging secrets.

### 7. Validate as much as possible

Run:

```bash
git diff --check
bash -n deploy.sh
```

If `yamllint` is available, run it. If it is not available, do not install anything just for this task. Instead, visually inspect the workflow and mention that `yamllint` was unavailable in the outbox report.

Do not run the GitHub Actions workflow yet.

### 8. Create outbox report

Create:

```text
outbox/0003-create-github-actions-ec2-control-workflow-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 9. Commit changes

If possible, commit with:

```bash
git add .github/workflows/cookbook-ec2-control.yml docs/aws-github-oidc-policy.md docs/github-actions-deploy-workflow.md outbox/0003-create-github-actions-ec2-control-workflow-results.md
git commit -m "mailbox: complete task 0003 github actions ec2 control workflow"
```

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `.github/workflows/cookbook-ec2-control.yml` exists.
- The workflow supports `status`, `start`, `deploy`, `restart`, and `stop`.
- The workflow uses GitHub OIDC, not static AWS keys.
- The workflow uses SSM Run Command, not SSH.
- Secrets are referenced only through GitHub Actions secret context.
- Documentation exists for GitHub Actions deployment.
- Documentation exists for AWS OIDC policy setup.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
