# Task 0001: Bootstrap Coder GitHub repo access and mailbox workflow

## Goal

Prepare this repository for the GitOps mailbox workflow.

The intended workflow is:

1. ChatGPT writes task prompts into `inbox/`.
2. Codex reads the newest task from `inbox/`.
3. Codex performs the work in the repo.
4. Codex writes a completion report into `outbox/`.
5. Codex commits all changes with a clear commit message.

This first task is about validating repo access, creating the baseline mailbox structure, and documenting how this Coder workspace should interact with GitHub.

## Important rules

- Do not commit secrets.
- Do not create fake secrets.
- Do not hardcode AWS keys, Cloudflare tokens, OpenAI API keys, GitHub tokens, or domain credentials.
- If authentication is missing, document the exact manual steps needed rather than inventing credentials.
- Use GitHub Actions secrets and variables for deployment secrets.
- Prefer GitHub OIDC for AWS authentication instead of static AWS access keys.
- Keep the implementation simple and understandable.

## Current project context

This repo will eventually deploy Vanilla Cookbook to AWS Free Tier using:

- Coder for the development workspace.
- Codex as the coding agent inside the Coder container.
- GitHub as the source repo and workflow engine.
- GitHub Actions as the secrets and deployment control plane.
- AWS EC2 as the small runtime VM.
- Docker Compose for running Vanilla Cookbook.
- Cloudflare Tunnel for exposing the app.
- Custom domain: `cookbook.roadmap.links`.

Vanilla Cookbook should eventually run on port 3000 behind Cloudflare Tunnel.

## Work to perform

### 1. Inspect repo and GitHub access

Run safe inspection commands only:

pwd
ls -la
git status
git remote -v
git branch --show-current
git log --oneline -5 || true
gh auth status || true
