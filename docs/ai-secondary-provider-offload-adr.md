# AI Secondary Provider Offload ADR

## Status

Accepted for docs-only evaluation planning. Runtime integration is not implemented. Secondary/offload providers remain disabled by default.

## Context

The current primary and final-answer provider baseline is the existing OpenAI `gpt-5.4-nano` path with the calibrated `0030L` through `0030O` live-eval behavior.

Current comparison baseline:

```text
status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495
```

The next possible cost-control question is whether a future secondary provider could help with bounded, low-risk sub-tasks without changing the current final-answer path.

`GLM-4.7 Flash` is only a candidate provider name in this task. This ADR does not claim verified pricing, API compatibility, context window, rate limits, quality, privacy policy, retention policy, or availability. Those facts must be verified before any later implementation task.

The existing local/operator controls from `0029C` through `0029I` and the locked `0029/0030` regression baseline remain the guardrails for any future provider experiment:

- operator gate;
- invite-only demo sessions;
- provider budget guard;
- usage reporting;
- public-route exposure review;
- monetization and entitlement boundary;
- offline and live-eval baselines.

## Decision

- The primary and final-answer provider remains the current OpenAI `gpt-5.4-nano` path unless a later approved task changes it.
- A future secondary provider, including a possible `GLM-4.7 Flash` candidate, may only be considered for bounded offload or advisory sub-tasks.
- Secondary/offload outputs must remain advisory inputs, not final user-visible answers.
- Final answer generation, citation faithfulness decisions, safety decisions, admin decisions, and provider budget decisions must not be delegated to an unproven secondary provider.
- No GLM runtime integration, SDK dependency, API call, routing change, fallback behavior, or public exposure is implemented in this task.
- Any future secondary provider must still respect operator, invite, budget, and reporting controls where those controls apply.
- A free or low-cost provider still has cost-like risks: privacy, quota, latency, failure mode, and quality regression.

## Allowed Offload Task Classes

These are candidate future task classes only. Each requires downstream validation and safe fallback to the existing primary baseline.

| Task class | Why low risk | Allowed input data | Must not receive | Required downstream validation | Fallback behavior |
| --- | --- | --- | --- | --- | --- |
| `query_expansion` | Expands retrieval queries without writing the final answer. | Short user question, normalized ingredient/topic terms, bounded public dataset vocabulary. | Raw provider prompts, API keys, operator tokens, full private recipe corpus, hidden admin state. | Terms must stay on-topic, bounded, and non-sensitive. Unrelated expansions are discarded. | Use original retrieval query only. |
| `ingredient_synonym_expansion` | Helps retrieval recall while remaining easy to verify. | Ingredient names, cuisine tags, safe normalization hints. | Private user notes, session tokens, unpublished recipes, policy state. | Synonyms must map to known ingredient concepts and stay food-related. | Use existing deterministic normalization only. |
| `dataset_metadata_cleanup_suggestions` | Suggests non-final cleanup ideas rather than mutating stored data. | Public dataset titles, tags, short metadata snippets, citation IDs. | Raw dataset files, private notes, any write-back channel. | Suggestions must remain advisory and require deterministic or operator review before use. | Ignore suggestion and keep source metadata unchanged. |
| `title_or_slug_suggestions` | Rephrases already grounded content without changing recipe facts. | Grounded recipe title, short ingredient list, existing citation IDs. | Unverified health claims, private data, final published title without validation. | Suggestions must remain grounded and avoid unsupported claims. | Keep current title or deterministic slug. |
| `non_final_clarification_candidate_generation` | Produces one optional question candidate rather than making the final decision. | Safe requirement summary, unresolved fields, workflow label. | Private data requests, user identity data, payment state, medical inference. | Candidate must be relevant, non-invasive, and still pass the existing clarification policy. | Use existing deterministic clarification logic. |
| `context_compression_draft_with_citation_ids_preserved` | Compresses bounded context while keeping provenance anchors explicit. | Retrieved snippets, citation IDs, safe support metadata. | Raw provider responses, secret env data, unpublished private recipes. | All required citation IDs must be preserved and no invented IDs may appear. | Use the uncompressed primary context packer. |
| `draft_critique_against_quality_checklist` | Reviews a draft against a fixed checklist without becoming the final answer. | Draft summary, quality checklist, citation IDs, warnings. | Final publish/write action, admin state, safety override authority. | Critique must stay checklist-shaped and may not output the final recipe or final answer. | Ignore critique and continue with primary draft evaluation only. |
| `formatting_only_rewrites_where_factual_content_is_already_fixed` | Cosmetic cleanup is easier to compare against the original text. | Already approved grounded text, formatting instructions, citation IDs. | Authority to change facts, add citations, or remove warnings. | Output diff must preserve facts, citations, and warnings. | Keep the original primary text. |

## Blocked Task Classes

These remain blocked for any future secondary-provider experiment unless a later ADR and implementation task changes the rule.

- `final_user_answer_generation`
  Reason: the final user-visible answer remains on the primary provider path.
- `final_recipe_draft_generation`
  Reason: recipe correctness, grounding, and support labeling remain primary-provider responsibilities.
- `food_safety_advice`
  Reason: safety-critical guidance must not move to an unverified secondary provider.
- `medical_allergy_diet_nutrition_claims`
  Reason: unsupported or unsafe claims create disproportionate risk.
- `citation_truth_or_faithfulness_final_decisions`
  Reason: provenance decisions must remain in the validated primary path.
- `safety_refusal_decisions`
  Reason: refusal boundaries are core safety behavior, not an advisory side-task.
- `admin_operator_decisions`
  Reason: operator/admin actions must not depend on an untrusted advisory provider.
- `provider_budget_decisions`
  Reason: budget enforcement is a guardrail, not a model suggestion.
- `invite_session_security_decisions`
  Reason: invite, session, and security checks remain deterministic local controls.
- `private_user_recipe_data_processing_without_explicit_future_privacy_decision`
  Reason: privacy review must happen before private data leaves the existing boundary.
- `any_task_that_can_publish_or_persist_data`
  Reason: this ADR is strictly pre-runtime and advisory-only.

## Privacy And Data-Boundary Policy

- Any future secondary/offload path must default to the smallest task-local payload possible.
- Offload candidates must prefer normalized terms, short summaries, bounded snippets, and citation IDs over raw full documents.
- Raw prompts, raw provider responses, API keys, operator tokens, invite/session tokens, `.env` content, admin state, and local paths must never be sent.
- Private saved-recipe content must remain blocked unless a later privacy decision explicitly allows a narrower use case.
- Public dataset content is lower risk than private cookbook content, but still requires bounded payload rules.
- Secondary-provider experiments must document retention, training, and data-handling policy before implementation.

## Budget And Usage-Reporting Policy

- No secondary-provider runtime budget logic is implemented in this task.
- Any future offload provider must have separate meter visibility so operator reports can distinguish primary versus secondary activity.
- Estimated savings discussed in docs or evals are offline estimates only, not billing truth.
- Secondary-provider usage must not reduce or weaken primary-provider budget enforcement.
- Final provider-call allow/block decisions remain with the existing budget-guard path.
- Future usage reporting must preserve safe serialization and must not log raw prompts, raw responses, keys, or local paths.

## Fallback And Failure Behavior

- If a secondary/offload output is missing, malformed, low quality, privacy-violating, or unsupported, the system must ignore it and continue with the existing primary baseline.
- There is no automatic user-visible fallback switching in this ADR.
- Advisory offload output must never become the sole source of truth for a final answer.
- Compression tasks that drop or invent citation IDs must be rejected.
- Clarification candidates that ask for irrelevant or private data must be rejected.
- Critique outputs that try to become the final answer must be rejected.
- Any future provider outage or quota issue must degrade safely to the current primary or deterministic path.

## Evaluation Plan

- Keep `GLM-4.7 Flash` evaluation docs-first and offline in this task.
- Use deterministic simulated offload outputs only.
- Compare future proposals against the current OpenAI baseline:

```text
status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495
```

- Add an offline harness that:
  - loads fixture cases;
  - validates allowed task classes versus blocked classes;
  - rejects invented citation IDs;
  - verifies citation-ID preservation for compression;
  - rejects unsupported claims and private-data requests;
  - verifies fallback-to-primary-baseline behavior is explicit;
  - verifies advisory-only behavior.
- Keep normal validation offline and mock-only.
- Do not add live OpenAI or live GLM calls to repository validation.

## Future Implementation Gates

No runtime implementation should begin until all of these are explicitly approved:

1. Provider facts are verified from primary documentation:
   pricing, API surface, availability, rate limits, context limits, privacy, and retention.
2. A follow-on ADR defines exact request routing, failure policy, and data boundary.
3. Operator, invite, budget, and usage-report integration points are specified.
4. A task-class allowlist is finalized with payload examples and rejection cases.
5. Offline evals show stable benefit without harming the current OpenAI baseline.
6. Live evaluation remains explicit opt-in and budget-bounded.
7. Public-route, auth, storage, and monetization boundaries remain unchanged unless separately approved.

Optional future config names may exist in docs only and must remain unwired in runtime request flow until a later task:

```env
AI_SECONDARY_PROVIDER_ENABLED=false
AI_SECONDARY_PROVIDER=glm
AI_SECONDARY_MODEL=glm-4.7-flash
AI_SECONDARY_PROVIDER_BASE_URL=
AI_SECONDARY_PROVIDER_API_KEY=
AI_OFFLOAD_TASKS=query_expansion,context_compression,title_suggestions
AI_FINAL_PROVIDER=openai
```

## Non-Goals

- No GLM provider runtime integration.
- No GLM API calls.
- No GLM SDK dependencies.
- No runtime secondary-provider routing or fallback.
- No production provider selection changes.
- No public route exposure.
- No production auth.
- No durable storage.
- No payment, ad, sponsor, or affiliate runtime behavior.
- No live provider calls during normal validation.
