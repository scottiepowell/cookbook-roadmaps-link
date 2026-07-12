# AI Secondary Provider Fact Register

## Purpose

This register records what must be verified from primary provider documentation before any future secondary/offload provider runtime adapter can start.

This task does not implement provider runtime behavior. It records facts, verification status, and the current implementation gate decision only.

## Baseline

Current final-answer baseline:

```text
OpenAI gpt-5.4-nano final-answer path
status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495
```

The corrected 0030 baseline, including the `0030P` no-bake cheesecake clarification fix, remains part of the comparison floor for any future provider experiment.

## Candidate Summary

- Provider candidate: GLM
- Candidate model: GLM-4.7 Flash
- Purpose: possible future secondary/offload provider for bounded low-risk tasks
- Current implementation status: not implemented
- Verification status: unverified unless primary documentation is actually available
- Implementation gate: blocked unless all required facts are verified

## Verification Rule

This register does not invent provider facts.

For this task, `GLM-4.7 Flash` remains:

```text
verification_status: unverified
implementation_gate: blocked
reason: primary provider documentation was not available in this task
```

## Register

| Fact category | Value | Verification status | Notes |
| --- | --- | --- | --- |
| `provider_identity` | `GLM` | `unverified` | Candidate name only. |
| `model_identifier` | `GLM-4.7 Flash` | `unverified` | Candidate model name only. |
| `primary_documentation_references` | `unverified` | `unverified` | No primary provider documentation was provided in this task. |
| `api_protocol_and_auth` | `unknown` | `unverified` | Runtime adapter work is blocked until primary docs confirm protocol and auth requirements. |
| `request_response_schema` | `unknown` | `unverified` | No request/response contract is approved. |
| `structured_output_support` | `unknown` | `unverified` | Must be verified from primary docs before any structured adapter work. |
| `streaming_support` | `unknown` | `unverified` | Not assumed. |
| `context_window` | `unknown` | `unverified` | Not assumed. |
| `max_output_tokens` | `unknown` | `unverified` | Not assumed. |
| `rate_limits` | `unknown` | `unverified` | Not assumed. |
| `quota_behavior` | `unknown` | `unverified` | Not assumed. |
| `pricing_input_tokens` | `unknown` | `unverified` | No pricing is recorded without primary docs. |
| `pricing_output_tokens` | `unknown` | `unverified` | No pricing is recorded without primary docs. |
| `free_tier_or_trial_terms` | `unknown` | `unverified` | Not assumed. |
| `privacy_policy` | `unknown` | `unverified` | Private user recipe data stays blocked by default. |
| `data_retention_policy` | `unknown` | `unverified` | Must be verified before any private or semi-private payload is considered. |
| `training_data_use_policy` | `unknown` | `unverified` | Must be verified before any future runtime proposal. |
| `regional_availability` | `unknown` | `unverified` | Not assumed. |
| `account_and_billing_requirements` | `unknown` | `unverified` | Must be verified before any implementation task. |
| `safety_policy_or_usage_restrictions` | `unknown` | `unverified` | No policy compatibility claim is made here. |
| `timeout_and_retry_guidance` | `unknown` | `unverified` | No runtime retry policy is approved. |
| `error_response_shape` | `unknown` | `unverified` | Must be documented before adapter work. |
| `logging_redaction_requirements` | `not approved` | `unverified` | Runtime logging rules remain undefined for this candidate. |
| `allowed_offload_tasks` | `query_expansion`, `ingredient_synonym_expansion`, `dataset_metadata_cleanup_suggestions`, `title_or_slug_suggestions`, `non_final_clarification_candidate_generation`, `context_compression_draft_with_citation_ids_preserved`, `draft_critique_against_quality_checklist`, `formatting_only_rewrites_where_factual_content_is_already_fixed` | `approved at ADR level only` | These come from `0031A` as candidate task classes, not verified provider capabilities. |
| `blocked_tasks` | `final_user_answer_generation`, `final_recipe_draft_generation`, `food_safety_advice`, `medical_allergy_diet_nutrition_claims`, `citation_truth_or_faithfulness_final_decisions`, `safety_refusal_decisions`, `admin_operator_decisions`, `provider_budget_decisions`, `invite_session_security_decisions`, `private_user_recipe_data_processing_without_explicit_future_privacy_decision`, `any_task_that_can_publish_or_persist_data` | `approved` | These remain blocked by policy. |
| `fallback_requirements` | `Fall back to the current OpenAI gpt-5.4-nano final-answer baseline and ignore bad or missing secondary output.` | `approved at ADR level only` | This is the current policy requirement, not a verified provider capability. |
| `verification_owner_or_method` | `future manual verification from primary provider documentation` | `unverified` | Requires a separate verification pass with source references. |
| `verification_date` | `unverified` | `unverified` | No primary-doc verification date exists for this task. |
| `implementation_gate_decision` | `blocked` | `current` | Runtime adapter work is blocked. |

## Current Decision

- `GLM-4.7 Flash` remains a candidate name only.
- No provider pricing, API, privacy, retention, quota, or availability fact is treated as verified here.
- Future runtime adapter work is blocked until the implementation gate in [AI Secondary Provider Implementation Gate](ai-secondary-provider-implementation-gate.md) is satisfied.

## Non-Goals

- No GLM SDK installation
- No GLM API calls
- No runtime provider adapter
- No secondary-provider routing
- No automatic fallback
- No production provider changes
