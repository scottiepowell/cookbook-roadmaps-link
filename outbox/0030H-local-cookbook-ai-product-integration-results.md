# 0030H Local Cookbook AI Product Integration Results

## Summary

Vanilla Cookbook remains an external Docker image on local port 3000 and the
AI workflows remain in the FastAPI sidecar on port 8000. The selected local
integration pattern is a sidecar-served product shell, preserving that boundary
without vendoring or rewriting the upstream frontend.

## Delivered

- Added `/product` as the obvious local starting point, with Cookbook and AI
  destinations, readiness/provider status, and fixture reset guidance.
- Added `/product/cookbook` for the local upstream-container target and
  `/product/ai` for the existing `/demo` workspace.
- Kept `/demo` unchanged and reused it for Recipe Creator/Session Alpha, Ask,
  Dataset, and Meal Planner workflows.
- Updated the local start script, mock smoke, README, UI plan, runbook,
  feature status, and backlog.
- Added deterministic route/static tests for the product shell and safe assets.

## Validation and boundaries

Normal validation stays offline and mock-only. Live wrappers skip unless
explicitly opted in; no live OpenAI call is required. No AWS, Terraform, CDK,
CloudFormation, DNS, Cloudflare, production deployment/auth/payment, public
routing, upstream UI rewrite, vector database, embeddings, raw dataset,
screenshots, browser automation, persistent index, or disk cache work was
added.

AWS/platform planning should resume only after this local product entry point,
startup guidance, and mock smoke coverage remain the reviewed baseline.
