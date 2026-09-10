# 0035L Git Bash Public Stack Launcher Results

Status: implemented; end-to-end startup verification blocked by host Docker
Desktop runtime state.

## Delivered

- Added `scripts/start-public-cookbook.sh` for Windows Git Bash.
- Starts Docker Desktop when its Linux engine is unavailable and waits with a
  bounded timeout.
- Validates the existing ignored sidecar and external-core environment files
  without reading or printing their contents.
- Ensures the existing public Docker network and named volumes, validates
  `docker-compose.public.yml`, starts the public core and AI sidecar, and starts
  the provisioned Cloudflare connector when present.
- Reports only image, container health, and HTTP status outcomes.
- Detects an early Docker Desktop exit and reports the known stale
  `dockerInference` recovery path instead of waiting for the full timeout.

## Validation

- Git Bash syntax validation: passed.
- Focused launcher contract test: passed.
- Repository validation: passed (489 tests, 39 offline eval cases, Compose
  configuration, whitespace, links, domain guard, and secret-pattern scan).
- End-to-end host startup: blocked. Docker Desktop exits while removing its
  `dockerInference` runtime socket because the Windows WSL service retains an
  inaccessible stale entry. A normal WSL shutdown did not release it, and the
  current process cannot restart the Windows service without elevation.
- No Compose services, provider calls, recipe writes, or deployment mutations
  were attempted after Docker engine readiness failed.

## Safety

No credential, environment value, prompt, provider output, token, cookie,
session value, browser artifact, database path, or ignored runtime data was
printed, copied, staged, or committed.
