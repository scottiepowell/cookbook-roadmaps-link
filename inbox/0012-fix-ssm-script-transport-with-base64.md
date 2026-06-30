# Task 0012: Fix SSM Script Transport With Base64

## Goal

Fix the GitHub Actions deployment workflow so the Bash deploy and restart scripts are transported to Systems Manager safely without relying on inline `bash -lc <quoted multiline script>` quoting.

Task 0011 changed the workflow to use:

```bash
remote_command="$(printf 'bash -lc %q' "$remote_script")"
```

The original `/bin/sh` `pipefail` error is gone, but the deploy still fails before Bash runs:

```text
/var/lib/amazon/ssm/.../_script.sh: 2: Syntax error: Unterminated quoted string
failed to run commands: exit status 2
```

Root cause: `AWS-RunShellScript` still writes/executes a command string through `/bin/sh` first. `printf %q` creates Bash-oriented quoting that can break when parsed by `/bin/sh` before `bash -lc` receives it.

## Current environment

- Repository: `scottiepowell/cookbook-roadmaps-link`
- Branch: `main`
- AWS region: `us-east-2`
- Current EC2 instance ID: `i-0e5458adbc0663914`
- EC2 is Online in Systems Manager Fleet Manager.
- Manual EC2 bootstrap/preflight already passed.
- GitHub Actions `status` passed.
- GitHub Actions `deploy` reaches SSM but fails in remote command parsing.

## Important rules

- Do not commit secrets.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, or deployment commands.
- Do not change GitHub repository settings.
- Only modify repo files and local validation/docs as needed.

## Required fix

Update `.github/workflows/cookbook-ec2-control.yml` to stop using `printf 'bash -lc %q'` for the deploy and restart remote payloads.

Use a safer transport pattern:

1. Build the Bash script body on the GitHub runner as `remote_script`.
2. Base64 encode the entire script body on the GitHub runner, for example:

   ```bash
   remote_script_payload="$(printf '%s' "$remote_script" | base64 -w 0)"
   ```

3. Send a POSIX-`sh` compatible `remote_command` to SSM that:

   - creates a temporary file under `/tmp`,
   - writes the decoded script into that file,
   - chmods it,
   - runs it with Bash explicitly,
   - removes it afterward.

   Example pattern:

   ```bash
   remote_command="$(cat <<EOF
   set -eu
   script_tmp=\$(mktemp /tmp/cookbook-ssm.XXXXXX.sh)
   trap 'rm -f "\$script_tmp"' EXIT
   printf '%s' '$remote_script_payload' | base64 --decode > "\$script_tmp"
   chmod 0700 "\$script_tmp"
   bash "\$script_tmp"
   EOF
   )"
   ```

4. Keep the existing secret-safe `.env` payload behavior. The `.env` payload may remain separately base64 encoded as it is today.
5. Apply this fix to both:

   - `deploy` action SSM payload
   - `restart` action SSM payload

## Quoting requirements

The command passed to SSM must be safe for `/bin/sh` to parse. The Bash-only content must live inside the base64-decoded temporary script and must not be parsed by `/bin/sh` directly.

Avoid:

```bash
bash -lc <large quoted multiline script>
printf %q
$'...'
```

Prefer:

```bash
printf '%s' '<base64-script>' | base64 --decode > "$script_tmp"
bash "$script_tmp"
```

## Documentation updates

Update the troubleshooting note added in task 0011 to say:

- Symptom 1: `set: Illegal option -o pipefail` means the payload ran under `/bin/sh`.
- Symptom 2: `Syntax error: Unterminated quoted string` means inline quoting broke before Bash ran.
- The workflow avoids both by base64 transporting the Bash script and executing it with `bash` from a temporary file.

## Validation

Run local validation only:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Also inspect the workflow and confirm:

- There is no remaining `printf 'bash -lc %q'` usage.
- Deploy remote script is base64 transported and run with `bash "$script_tmp"`.
- Restart remote script is base64 transported and run with `bash "$script_tmp"`.

Do not run AWS, Cloudflare, OpenAI, or deployment commands as part of this task.

## Outbox report

Create:

```text
outbox/0012-fix-ssm-script-transport-with-base64-results.md
```

Include:

- Summary of the new failure and the fix.
- Files changed.
- Exact validation commands run.
- Confirmation that `printf 'bash -lc %q'` was removed.
- Confirmation that deploy/restart now base64 transport the Bash script and execute it from a temp file with Bash.
- Any assumptions.
- Any blockers.
- Recommended next operator action.

## Commit

Commit with:

```bash
git add .github/workflows/cookbook-ec2-control.yml docs/ outbox/0012-fix-ssm-script-transport-with-base64-results.md
git commit -m "mailbox: complete task 0012 fix ssm script transport with base64"
```

If only a subset of docs changed, stage only the actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- Deploy no longer uses inline `bash -lc` quoting for the large remote script.
- Restart no longer uses inline `bash -lc` quoting for the large remote script.
- Deploy transports the Bash script body as base64, decodes it to a temp script on EC2, and runs it with Bash.
- Restart transports the Bash script body as base64, decodes it to a temp script on EC2, and runs it with Bash.
- Secret-safe `.env` rendering behavior is preserved.
- Documentation explains both SSM shell/quoting failure modes.
- Local validation passes.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
