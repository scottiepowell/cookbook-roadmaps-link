# 0033C SSO And BYOS Identity/Storage Architecture ADR

## Goal

Investigate account access through SSO/email registration and a BYOS model where users can store their own Cookbook data in their own cloud storage, such as Google Drive, Dropbox, or similar providers.

This is an ADR/research task only. Do not implement SSO, OAuth, email registration, or cloud-storage integration in this task.

## Context

The product direction is to allow persistence without making the Cookbook application the primary long-term owner of user data. Large identity/storage providers may act as both login providers and user-owned storage providers.

## Required Work

Create:

```text
docs/sso-byos-identity-storage-architecture-adr.md
```

The ADR should cover:

- problem statement;
- identity options: email registration, Google, Facebook/Meta, and other likely providers;
- BYOS concept: user-owned cloud storage for recipe/application data;
- how identity and storage grants relate but remain separable;
- OAuth/OIDC consent and scope boundaries;
- data ownership and portability goals;
- what data could be stored in BYOS vs what the app may still need locally;
- offline/local fallback considerations;
- token handling and refresh-token risk;
- user revocation and account deletion behavior;
- import/export behavior;
- privacy, security, and compliance considerations;
- provider dependency risks;
- UX expectations;
- staged implementation options;
- contract test strategy;
- explicit non-goals.

If internet access is available, research current high-level provider constraints and documentation for likely SSO/BYOS providers. If internet access is not available, state the limitation and keep the ADR conceptual.

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Create:

```text
outbox/0033C-sso-byos-identity-storage-architecture-adr-results.md
```

## Acceptance Criteria

- ADR exists.
- ADR treats SSO and BYOS as architecture decisions, not implemented behavior.
- ADR defines identity/storage boundaries and user-owned data goals.
- ADR identifies consent, token, revocation, and deletion risks.
- ADR preserves app data safety and existing mock/offline validation.
- No provider SDKs, auth endpoints, storage API clients, migrations, secrets, or live integrations are added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

## Commit

```bash
git add docs README.md outbox/0033C-sso-byos-identity-storage-architecture-adr-results.md
git commit -m "docs: add sso byos identity storage adr"
git pull --rebase origin main
git push origin main
```
