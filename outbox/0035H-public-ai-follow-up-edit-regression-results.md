# 0035H Public AI Follow-Up Edit Regression Results

## Result

Complete and deployed.

The public AI-first flow keeps an existing recipe chat on its core-owned opaque
sidecar interaction for ordinary serving edits, ingredient substitutions, and
compound edits. A candidate only commits after the requested yield and every
requested substitution are present; otherwise the prior draft and successful
change count remain unchanged. Retained-draft follow-up failures now use
follow-up-specific copy rather than initial-recipe clarification copy.

Replacement confirmation remains unchanged. A likely new dish pauses without
mutating the current draft or consuming a change; confirmed replacement still
begins from a clean new session.

## Files changed

- Sidecar session classification, serving recognition, substitution commit
  guard, retry guidance, focused tests, public Compose image pins, mailbox, and
  AI feature documentation.
- External core safe chat-response mapping and public proxy regression tests.

## Safe validation outcomes

- Existing-draft compound edit regression: passed.
- Separate substitution and serving-edit regressions: passed.
- Compound partial-candidate prevention: passed.
- Replacement confirmation regressions: passed.
- Focused sidecar session, requirements, and serving tests: 87 passed.
- Focused core proxy, save, and entry tests: 24 passed.
- Full sidecar repository tests: 475 passed.
- Offline evaluations: 39 passed.
- Compose configuration validation: passed.
- Sidecar image build: passed.
- Core production image build: passed.
- Public containers: started; sidecar healthy.
- Public HTTPS health: 200.

## Deployment

- Public core image: `local/vanilla-cookbook-adapter:0035h`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035h`.
- External core branch: `openclaw/0035H-public-ai-follow-up-edit-regression`.
- External core commit: `73f5d1c2e73b39f932ac4c51f0a849842cd25ed8`.

No live provider request or signed-in recipe mutation was performed. No
secrets, prompts, raw provider output, cookies, tokens, session values, local
environment values, database paths, browser artifacts, or ignored runtime data
were staged.
