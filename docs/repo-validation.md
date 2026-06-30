# Repository Validation

The **Repository Validation** GitHub Actions workflow runs on pushes, pull requests, and manual dispatches. It calls `scripts/validate-repo.sh`, uses only read access to repository contents, and requires no GitHub Actions secrets.

## Checks

The validator:

- runs `bash -n` on `deploy.sh` and every shell script directly under `scripts/`;
- copies `.env.example` to a disposable directory and renders the Docker Compose configuration without starting containers;
- runs `ai-api` tests in a temporary Python virtual environment when the sidecar exists;
- checks working-tree, staged, tracked, and untracked repository files for whitespace errors;
- verifies that inline local Markdown links point to files that exist;
- fails active files that reintroduce the former singular-roadmap Cookbook hostname or base domain while preserving historical mailbox records;
- scans text files for obvious AWS access key IDs, GitHub token prefixes, OpenAI key prefixes, private key headers, and token-like Cloudflare assignments.

Temporary Compose files are removed automatically. The validator never prints `.env` content or matched credential text.

## Run Locally

Docker with the Compose plugin, Git, Bash, Perl, Python, and network access for
Python package installation are required:

```bash
cd /home/coder/repo
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
```

Run validation before committing a mailbox result and before using deployment-related changes.

## Secret-Pattern Scan

The scan is a fast safety net for obvious committed credentials, not a complete secret-management or history-audit product. It scans current repository text and reports only the rule name and filename. Placeholder setting names such as `AWS_ROLE_ARN` and `CLOUDFLARE_TUNNEL_TOKEN` do not fail unless they are paired with a token-like value.

For a false positive, first confirm the value is non-sensitive. Prefer replacing realistic examples with explicit placeholders. If a new legitimate format still conflicts, narrow the rule in `scripts/validate-repo.sh` and document the reason in the mailbox result; do not add a broad bypass that hides real credentials. If a real secret is found, revoke or rotate it before removing it from the repository and history.

## CI Scope

This workflow does not deploy, start containers, contact cloud APIs, or require AWS, Cloudflare, OpenAI, or application credentials. It validates repository content, local Compose parsing, and offline AI sidecar tests.

## GitOps Mailbox Support

Mailbox changes become deployment inputs after review and commit. Running the same script locally and in CI gives each `inbox/` task and `outbox/` result a consistent quality gate before the desired state reaches the manual deployment workflow.
