# Cookbook usage reports through Resend

The sidecar records provider-reported OpenAI input, output, and total tokens in
a dedicated SQLite database. It records each completed provider call and failed
call, including usage returned with malformed structured output. Budget guard
estimates are not substituted for actual usage. Failed requests without usage
remain unknown. SDK-internal retries are not counted individually.

This covers Cookbook sidecar OpenAI calls only, not account-wide provider usage.
Core authentication, users, sessions, and recipes remain in the external core.
Login metrics and cost estimates are deferred until their definitions are agreed.
No prompts, recipe text, account identity, tokens, or credentials are recorded.

## Configure

Create ignored `.env.reporting` in this repository with these names:

```dotenv
AI_REPORT_EMAIL_ENABLED=false
RESEND_API_KEY=
AI_REPORT_FROM=
AI_REPORT_TO=
```

Use a Cookbook-specific Resend API key, a sender on your verified sending domain,
and one intended recipient. Never copy configuration from the concessions app.
Only the one-off report container receives email configuration. The AI API gets
the database path but no Resend credentials. The recipient and cadence must be
agreed before enabling sending or scheduling.

The integration uses [Resend's email API](https://resend.com/docs/api-reference/emails/send-email)
and [idempotency keys](https://resend.com/docs/dashboard/emails/idempotency-keys).
Resend's acceptance is not proof of inbox delivery; verify delivery in its
dashboard and the recipient inbox during the first authorized live check.

## Build and enable collection

Use the existing public Compose prerequisites: `PUBLIC_CORE_ENV_FILE` and
`PUBLIC_CORE_OIDC_ENV_FILE` point to the ignored external core `.env` and
`.env.public` respectively. Preserve `.env.public-ai` and existing volumes.

From the sidecar repository in Git Bash:

```bash
docker build -t local/cookbook-ai-sidecar:reports-v1 ai-api
docker compose -f docker-compose.public.yml -f docker-compose.reporting.yml config -q
docker compose -f docker-compose.public.yml -f docker-compose.reporting.yml up -d --no-deps ai-api
```

The Git Bash public-stack launcher includes the overlay when `.env.reporting`
exists. Include it explicitly for manual Compose launches. Omitting it stops recording;
it does not erase the `cookbook-usage-reports` volume. Back up that volume with
the existing operational backup process. Do not remove it with `down -v`.
Retention is currently indefinite; agree a retention policy before wider use.

## Preview or send

Use explicit timezone-aware boundaries; the start is inclusive and end exclusive.
For example, this previews one UTC day without calling Resend:

```bash
docker compose -f docker-compose.public.yml -f docker-compose.reporting.yml run --rm --no-deps usage-report --start 2026-09-10T00:00:00Z --end 2026-09-11T00:00:00Z
```

After the intended recipient and sender are configured and live sending is
authorized, set `AI_REPORT_EMAIL_ENABLED=true` in the ignored file and append
`--send` to the same command. The CLI also requires `--send` explicitly.
Use closed reporting periods when sending. A daily or weekly scheduler can call
this command with explicit period boundaries once cadence and timezone are agreed.
No scheduler is installed by this change.

The database is initialized by the first recorded provider call. Reports cannot
recover past usage, and previews fail clearly if recording has never initialized.
Reports expose the first recorded event and missing-usage counts. A storage
failure logs only `usage_record_failed` and does not interrupt recipe generation;
investigate these log events before treating period coverage as complete.

Accepted reports are persisted and never resent for the same period and sender/
recipient pair. Uncertain delivery retries reuse the original body and key even
if newer events arrive. Since Resend retains keys for 24 hours, automatic retry
is refused after 23 hours; reconcile with Resend before any manual recovery.
Do not delete delivery rows to work around an uncertain response.

## Validation and current status

- Docker image build passed.
- Twenty-one focused provider/reporting/launcher tests passed offline, with HTTP responses mocked.
- Running AI sidecar healthy; core health HTTP 200; Git Bash launcher syntax valid.
- Google sign-in: on September 10, 2026, the operator reported successful Continue
  with Google. The browser showed an authenticated Cookbook session. The public
  authorization route had the correct HTTPS callback, identity-only scopes,
  state, PKCE, and nonce. No authentication code change was necessary.
- Resend key, sender, recipient, and cadence are not yet configured in Cookbook.
- No real report was sent; provider delivery and inbox receipt remain unverified.
- Collection is enabled in the public sidecar using a dedicated persistent volume.
  The ignored reporting file has email disabled and blank credentials/addresses.
  Both Compose profiles validated with the existing ignored core environment files.

Test command:

```bash
docker run --rm --network none -v "$PWD:/workspace:ro" -e PYTHONPATH=/app local/cookbook-ai-sidecar:reports-v1 python -m pytest -p no:cacheprovider /workspace/ai-api/tests/test_usage_reporting.py /workspace/ai-api/tests/test_providers.py /workspace/ai-api/tests/test_public_stack_launcher.py -q
```
