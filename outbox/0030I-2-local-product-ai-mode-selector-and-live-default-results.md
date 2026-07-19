# 0030I-2 Local Product AI Mode Selector Results

Added a visible local product AI-mode preference with Live OpenAI selected by
default, a Mock offline toggle, and the sole approved live model
`gpt-5.4-nano`. The current provider runtime is process-wide, so the control
does not mutate it or silently reroute requests: it safely reports whether the
configured sidecar can honor Live OpenAI and tells the user when explicit live
opt-in/budget configuration is missing. Mock validation remains forced offline.

No API key, environment value, prompt, provider response, path, live call,
provider-routing overhaul, or production capability was added.
