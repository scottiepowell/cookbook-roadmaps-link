Title: 0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness Results

Summary

- Added a docs-first ADR for a possible future secondary/offload provider path.
- Added a deterministic offline eval harness with simulated secondary-provider outputs only.
- Kept the current OpenAI `gpt-5.4-nano` path as the final-answer baseline.
- Added no GLM runtime integration, routing, fallback, SDK, or live calls.

ADR Created

- Created `docs/ai-secondary-provider-offload-adr.md`.
- The ADR states that `GLM-4.7 Flash` is only a candidate provider name in this task.
- The ADR does not claim verified GLM pricing, compatibility, limits, quality, privacy policy, or availability.
- The ADR keeps the current baseline fixed at:
  - `status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495`

Allowed Task Classes

- `query_expansion`
- `ingredient_synonym_expansion`
- `dataset_metadata_cleanup_suggestions`
- `title_or_slug_suggestions`
- `non_final_clarification_candidate_generation`
- `context_compression`
- `draft_critique_against_quality_checklist`
- `formatting_only_rewrites_where_factual_content_is_already_fixed`

Blocked Task Classes

- `final_user_answer_generation`
- `final_recipe_draft_generation`
- `food_safety_advice`
- `medical_allergy_diet_nutrition_claims`
- `citation_truth_or_faithfulness_final_decisions`
- `safety_refusal_decisions`
- `admin_operator_decisions`
- `provider_budget_decisions`
- `invite_session_security_decisions`
- `private_user_recipe_data_processing_without_explicit_future_privacy_decision`
- `any_task_that_can_publish_or_persist_data`

Eval Harness Added

- Created `evals/ai_cookbook/secondary_provider_offload_cases.yaml`.
- Created `evals/ai_cookbook/secondary_provider_offload_eval.py`.
- The harness runs offline only, loads fixture cases, and checks:
  - allowlist versus blocked task classes;
  - advisory-only behavior;
  - primary final-answer provider stays OpenAI;
  - fallback behavior is explicit;
  - citation IDs are preserved for compression;
  - invented citation IDs are rejected;
  - unsupported claims are rejected;
  - private-data clarification requests are rejected;
  - critique outputs do not become final answers.

Tests Added

- Created `ai-api/tests/test_ai_secondary_provider_offload_docs.py`.
- Tests verify:
  - ADR existence and required sections;
  - OpenAI `gpt-5.4-nano` remains the final-answer baseline;
  - secondary/offload behavior is disabled and docs-only by default;
  - eval cases and runner exist;
  - the eval runner passes offline;
  - app runtime files do not add secondary-provider routing.

Docs Updated

- `docs/ai-secondary-provider-offload-adr.md`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Validation Results

- `python evals/ai_cookbook/secondary_provider_offload_eval.py`: passed
- `python -m pytest ai-api/tests/test_ai_secondary_provider_offload_docs.py -q`: passed
- `python evals/ai_cookbook/run_evals.py`: passed
- `python scripts/e2e-ai-29-30-regression.py`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-ai-env-file-loader.ps1`: passed
- `bash scripts/validate-repo.sh`: passed
- `git diff --check`: passed
- `docker compose config --quiet`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1`: skipped cleanly without live opt-in

Explicit Non-Goals

- No GLM runtime integration
- No GLM SDK dependency
- No GLM API calls
- No runtime secondary-provider routing
- No automatic model fallback
- No public route exposure
- No production auth
- No durable storage
- No payment, ad, or sponsor runtime behavior
- No live provider calls during normal validation

Artifact Safety Confirmation

- No `.env` file committed
- No provider key or key fragment committed
- No raw provider prompt committed
- No raw provider response committed
- No `.tmp-ai-demo` artifact committed
- No log or screenshot committed
- No local absolute path added to public docs examples by this task
- No GLM runtime code or secondary-provider routing added

Recommendation For The Next Task

- The next safe follow-on is a provider-fact verification and implementation-gate task that confirms candidate-provider pricing, privacy, retention, limits, and API behavior from primary documentation before any runtime adapter work starts.
