# Local Cookbook AI Product Acceptance Checklist

## Prerequisites and start

- Use the repository virtual environment and Docker Compose when the upstream
  Cookbook container is needed.
- Start the mock local product:

  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
  ```

- Open `http://127.0.0.1:8000/product` first. This is the canonical local
  entry point; `/demo` remains the direct AI workspace.

## Product checks

- Readiness shows provider mode/model, saved-recipe fixture status, dataset
  fixture status, and the mock/offline default.
- If a fixture is missing, restart `start-ai-demo-local.ps1`; do not add raw
  datasets to the repository.
- **Open Cookbook** redirects to the local upstream app on port 3000.
- **Open AI Recipe Creator** opens `/demo`, where importer, Ask My Cookbook,
  Dataset, Meal Planner, and Recipe Session Alpha remain available.

## Recipe Session Alpha checks

- Start a detailed cheesecake request and verify a draft with citations.
- Start `make dessert` and verify exactly one clarification question.
- Send `actually make it no-bake` after a baked draft and verify RAG refresh
  plus a revision summary.
- Send `thanks` and verify no RAG refresh; existing draft/citations are reused.
- Finalize for demo and verify the explicit demo-only, no-production-writeback
  warning.

## Safety and go/no-go

- Mock/offline mode is the normal acceptance path; do not enable live OpenAI.
- Product and readiness content must not expose secrets, prompts, provider
  responses, environment values, or local paths.
- Direct Windows pytest may fail on the known `pytest-of-scott` Temp ACL issue;
  use the Git Bash validator as the reliable full-suite check when it passes.
- Go for AWS/platform planning only when `/product`, redirects, readiness,
  Recipe Session Alpha flows, mock smoke, and offline validation all pass.
- No-go if the shell cannot guide an operator to recovery, fixture state is
  unsafe, redirects are wrong, or any production/public boundary is crossed.
