# AI Screenshot Capture Guide

Use this guide when creating future portfolio screenshots or demo captures for the AI cookbook work. Screenshots are deferred for now so this task stays documentation-only and avoids accidentally exposing local paths, provider keys, private recipe data, or account details.

## Screenshot Checklist

Capture from safe mock/demo data only:

- README AI showcase section.
- [AI Portfolio Showcase](ai-portfolio-showcase.md) architecture and validation sections.
- [AI Feature Status](ai-feature-status.md) matrix.
- AI demo UI readiness panel at `/demo`.
- AI demo UI answer cards with raw JSON collapsed.
- `scripts/demo-ai-mock.ps1` passing.
- Offline eval output from `evals/ai_cookbook/run_evals.py`.
- REST client examples from `scripts/demo-ai-requests.http` with generated fixture responses.
- Manual live smoke output only when it contains no key values, no raw provider config, and no private account details.
- Vanilla Cookbook homepage only if no private user or recipe data is visible.

## Safety Rules

Never show:

- provider API keys or key prefixes;
- `.env` file contents;
- authorization headers;
- Cloudflare token values;
- AWS account IDs, access keys, secret keys, session tokens, or role ARNs unless intentionally redacted;
- private recipe/user data;
- local private filesystem paths beyond the repository path already documented in task instructions;
- raw Kaggle dataset files or generated index artifacts;
- billing, usage, or dashboard screens with private account details.

Prefer:

- generated SQLite and CSV fixtures;
- mock provider output;
- cropped terminal output with only pass/fail lines;
- REST examples that use `http://127.0.0.1:8000`;
- manually redacted screenshots reviewed before commit.

## Useful Future Captures

1. Repository landing page showing the AI showcase.
2. Feature status matrix with completed workflows.
3. Sidecar demo UI readiness panel.
4. Sidecar demo UI importer or dataset RAG answer card.
5. Mock demo script output showing offline evals plus endpoint checks.
6. Offline eval output showing all cases passing.
7. REST request/response examples for importer, Ask My Cookbook, dataset ask, and meal planning.
8. Live smoke success summary with no surrounding environment output.

## Commit Rules

Before committing screenshots:

- inspect each image at full size;
- verify no secret, key prefix, token, private path, private recipe, billing detail, or account identifier is visible;
- keep screenshots small and focused;
- avoid generated artifacts from demo runs unless the task explicitly approves them;
- document exactly how each screenshot was produced.
