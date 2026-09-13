# Hosted Groq advisory pilot

Goal: [Issue #8](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/8)

Mailbox: [`0035M`](../inbox/0035M-hosted-groq-advisory-integration.md)

Date: 2026-09-13

The native Cookbook **Add a recipe** page includes a separate **Kitchen ideas**
panel. A signed-in user selects a task, enters up to 12 short lines, confirms
that the text is public or invented, and reviews optional suggestions. The
panel never reads saved recipes, sends a core account record, changes the
active recipe draft, or saves anything. Its authenticated core proxy forwards
only the chosen task and supplied text to the sidecar. The sidecar verifies the
operator token, task allowlist, input bounds, and non-sensitive text gate.

The sidecar uses a dedicated `GroqOffloadProvider` and the existing OpenAI
Python client with Groq's Chat Completions API. `openai/gpt-oss-20b` is pinned.
Every response uses strict JSON Schema. Local checks require each known source
ID exactly once, a bounded suggestion, and preserved numeric quantities for
ingredient, instruction, and plain-language tasks. A 429 or 5xx gets at most
one retry; three consecutive failures open a 60-second circuit. A failure
returns the original lines with `fallback` status. No second provider call is
made. The existing `gpt-5.4-nano` final recipe generation and save path is
unchanged.

| Native task | Pilot behavior |
| --- | --- |
| Recipe titles | Suggest one title per public dish idea. |
| Ingredient wording and units | Suggest parsing/normalization; numeric quantities must survive. |
| Instruction cleanup | Suggest clearer wording; numeric quantities must survive. |
| Optional substitutions | Suggest one candidate per ingredient, for user review. |
| Shopping aisle labels | Suggest a label for each supplied item; no purchase is added. |
| Pantry meal ideas | Suggest ideas from supplied shelf-stable ingredients; no freshness assessment. |
| Meal ideas | Suggest a meal from each supplied public title or ingredient set. |
| Plain-language rewrite | Suggest simpler wording; numeric quantities must survive. |
| Search wording | Suggest a synonym for each supplied public term. |

The ADR's remaining candidates were assessed against the current product:

- Retrieval reranking, context compression, no-match triage, clarification,
  and cache-plan suggestions would add a call before the trusted final recipe
  response or duplicate existing deterministic logic. They are not enabled
  without measured quality and token savings.
- Conversation compression, duplicate detection, and saved-recipe meal ranking
  need private canonical data. They remain blocked pending verified account
  zero-data-retention controls and a separate privacy review.
- Grounded FAQ, support routing, usage narratives, incident summaries, release
  notes, and synthetic eval critique are operator or development workflows,
  not native cooking interactions. They need approved source sets and separate
  review surfaces before product wiring.
- Final recipe/importer JSON, meal-plan JSON, food-safety and allergy decisions,
  account actions, and every write stay with the baseline or core authority.

The public Compose route loads `GROQ_API_KEY` from the **ignored canonical
sidecar `.env`** and pins `AI_OFFLOAD_ENABLED=true` plus the nine-task allowlist
for this pilot. The worktree needs no copied secret. Do not put the key in core
env files, GitHub Actions, screenshots, logs, commits, or an API response. The
core proxy limits each signed-in user to 10 attempts per 15 minutes, and the
sidecar's existing provider-call budget applies to Groq. Aggregate logs record
task, status, duration, and token counts only.

Groq's current [structured-output documentation](https://console.groq.com/docs/structured-outputs)
lists strict mode for `openai/gpt-oss-20b`; its
[compatibility guide](https://console.groq.com/docs/openai) documents the
OpenAI client base URL. Its [free-plan limits](https://console.groq.com/docs/rate-limits)
list 30 RPM, 1,000 RPD, 8,000 TPM, and 200,000 TPD for that model, subject to
account-specific settings. Its [data-controls guide](https://console.groq.com/docs/your-data)
says organization admins can enable zero data retention. The key's presence
and a successful generated-fixture call do **not** prove that this account has
ZDR enabled. Until that state is verified, test with public or invented text
only, even if a browser user is signed in. There is no production capacity or
private-data approval implied by this pilot.

To verify the browser route, sign in at `https://cookbook.roadmaps.link`, open
**Add a recipe**, expand **Kitchen ideas**, choose **Shopping aisle labels**,
enter `carrots`, check the public/invented-data box, and select **Get ideas**.
The resulting suggestion is review-only. The primary recipe chat above it
still creates and saves drafts through its established path.
