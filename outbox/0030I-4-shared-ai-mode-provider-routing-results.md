# 0030I-4 Shared AI Mode Provider Routing Results

Added `app.ai_mode_routing` as the shared safe request-mode resolver. It accepts
only mock/offline or live/openai, restricts live to `gpt-5.4-nano`, returns
safe unavailable categories for missing explicit opt-in/configuration, and
never exposes keys or environment values. Request schemas for importer,
recipe sessions, Ask, Dataset Ask, and Meal Planner now carry the same narrow
mode/model preference shape. No global provider mutation or silent live-to-mock
fallback is introduced; normal validation remains mock-only.
