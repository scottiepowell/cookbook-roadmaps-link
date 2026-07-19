# 0030I-3 AI Mode Selector Provider Wiring Results

The previous selector was display-only because the runtime provider is read
from process settings. Import requests now accept a narrow request-scoped mode
preference: mock resolves to `mock-basic`; live accepts only `gpt-5.4-nano`
and requires existing live opt-in plus an API key. Unavailable live requests
return a safe provider-unavailable error rather than silently falling back to
mock. The product preference is retained in browser local storage and `/demo`
now exposes a visible link back to `/product`.

This remains a narrow local integration. Other provider-backed routes retain
their existing process-scoped configuration pending a dedicated shared routing
task; no global mutable provider setting, budget bypass, secret exposure, live
call, or production capability was added.
