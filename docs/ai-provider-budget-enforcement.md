# AI Provider Budget Enforcement

## Purpose

This document describes the centralized provider-call budget guard used by the local AI demo surface. It sits after the optional local operator gate and before any live provider invocation.

The goal is simple: allow offline/mock flows by default, but stop live provider calls safely when the demo is globally disabled, the provider budget is exhausted, the token caps are exceeded, or the estimated cost budget is too tight.

## Relationship To The Schema Scaffold

`ai-api/app/ai_access_models.py` defines the safe data shapes used here:

- `AiProviderMeterEvent`
- `AiBudgetSnapshot`
- `AiProviderBudgetDecision`

`0029E` turns those shapes into a deterministic process-local guard and tracker. It does not add persistent storage, billing, or an admin dashboard.

## Relationship To The Operator Gate

`0029D` adds the local/private operator gate. That gate decides whether the workflow may enter the protected demo surface at all.

`0029E` runs after the operator gate and before provider invocation. A request can be:

- allowed by the operator gate, then blocked by budget;
- allowed by both, then sent to the provider;
- or skipped entirely for mock/offline workflows.

## Configuration

Recommended environment variables:

```text
AI_PROVIDER_CALLS_ENABLED=true
AI_PROVIDER_GLOBAL_DISABLE=false
AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION=10
AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL=12000
AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL=1200
AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL=14000
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION=1.00
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL=0.25
AI_PROVIDER_BUDGET_MODE=enforce
```

Rules:

- mock/local provider calls are treated as zero-cost and normally allowed;
- live provider calls fail closed when the configuration is invalid;
- the guard never logs or returns raw prompts, provider responses, API keys, Authorization headers, or local paths;
- if the global disable or provider-call disable flags are set, live calls are blocked before provider invocation.

## Decision Flow

The guard follows a deterministic order:

1. read centralized budget settings;
2. treat mock/local provider calls as zero-cost;
3. fail closed on invalid live budget configuration;
4. block if provider calls are globally disabled;
5. block if the estimated input token cap is exceeded;
6. block if the requested output token cap is exceeded;
7. block if the total estimated token cap is exceeded;
8. block if the session call-count cap is exhausted;
9. block if the per-call estimated cost cap is exceeded;
10. block if the session estimated cost cap is exhausted;
11. otherwise allow the provider call and record a safe meter event.

The helper returns an `AiProviderBudgetDecision` plus a safe `AiBudgetSnapshot` and `AiProviderMeterEvent`.

## Blocked Responses

When a live provider call is blocked, the caller should return a safe response that explains the budget reason without implying a provider call occurred.

Recommended messages include:

- `Provider calls are disabled for this local demo.`
- `Provider call budget exhausted for this demo session.`
- `Requested output token limit exceeds the configured demo cap.`
- `Estimated provider cost exceeds the configured demo budget.`

## Meter Events

`AiProviderMeterEvent` records allowed, blocked, skipped, or failed provider decisions.

The local tracker is process-local only. It exists so tests and demo scripts can observe call counts and estimated spend without writing to disk.

## Live Smoke And Eval Scripts

The live smoke and live eval wrappers should respect the centralized budget settings:

- skip cleanly when live opt-in is absent;
- skip cleanly when provider calls are disabled;
- fail safely when the budget configuration is invalid;
- use short-lived, local-only session keys for tracking.

The manual live importer path now recommends `AI_MAX_OUTPUT_TOKENS=900` because RAG-informed structured drafts need more output budget than tiny smoke tests.

## Non-Goals

This guardrail does not add:

- production storage;
- database migrations;
- auth;
- paid access;
- invite emails;
- payment integration;
- public route exposure;
- Redis, Postgres, or SQLite budget persistence;
- long-term memory;
- admin dashboard UI;
- live OpenAI calls during normal validation.
