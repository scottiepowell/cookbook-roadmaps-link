# 0035J Compose Deployment Validation for 0035I Results

## Result

Complete and deployed. 0035I remains unchanged and present at the validated
repository baseline.

## Environment resolution

The public Compose file requires `PUBLIC_CORE_ENV_FILE` and
`PUBLIC_CORE_OIDC_ENV_FILE`. The prior `.env.local` input did not exist. The
validation used the existing ignored core `.env` and `.env.public` inputs; no
placeholder file was created and no private value was read, logged, or staged.

## Validation

- `docker compose -f docker-compose.public.yml config -q`: passed.
- Existing required Docker network, volumes, and `0035i` image: present.
- Deployment-shaped Compose stack: started.
- Sidecar image and health: `local/cookbook-ai-sidecar:0035i`, healthy.
- Core image and status: `local/vanilla-cookbook-adapter:0035h`, running.
- Local core health and public HTTPS health: HTTP 200.
- External core source: unchanged.

No provider call, signed-in mutation, secrets, prompts, raw provider output,
cookies, tokens, session values, browser artifacts, database paths, local
private env values, or ignored runtime files were staged.
