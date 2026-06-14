# Cloudflare Tunnel And DNS Setup

Cloudflare Tunnel publishes Vanilla Cookbook without opening inbound web ports
on EC2. The `cloudflared` container makes an outbound connection to Cloudflare,
which forwards requests from the public hostname to the app on the private
Docker Compose network.

```text
Browser -> Cloudflare edge -> Cloudflare Tunnel -> cloudflared -> app:3000
```

Expected configuration:

```text
Public hostname: cookbook.roadmap.links
Service target:  http://app:3000
```

## Create The Tunnel

1. Sign in to the Cloudflare Zero Trust dashboard for the account containing
   the `roadmap.links` zone.
2. Open **Networks** > **Tunnels** and create a Cloudflared tunnel.
3. Give the tunnel a recognizable name such as `<COOKBOOK_TUNNEL_NAME>`.
4. Choose the Docker connector instructions and copy the generated tunnel token
   directly into the GitHub Actions secret `CLOUDFLARE_TUNNEL_TOKEN`.
5. Do not put the token in this repository, issue text, documentation, shell
   history, screenshots, or a GitHub Actions variable.

The repository's Compose service passes that secret to the official
`cloudflare/cloudflared` image at deployment time. `cloudflared` does not need
to be installed directly on the EC2 host.

## Configure The Public Hostname

In the tunnel's **Public Hostnames** configuration, add:

```text
Subdomain: cookbook
Domain:    roadmap.links
Type:      HTTP
URL:       app:3000
```

Cloudflare should create or manage the proxied DNS route for
`cookbook.roadmap.links` to the tunnel. Confirm the hostname appears under the
tunnel and in the zone's DNS records. Do not replace it with an A record that
points directly to the EC2 public IP.

Use `http://app:3000`, not `http://localhost:3000`. Inside the `cloudflared`
container, `localhost` means that same container. Compose DNS resolves the
service name `app` to the Vanilla Cookbook container on their shared network.

## Network Safety

- Do not expose EC2 port 3000 to the internet.
- Do not add inbound EC2 security-group rules for HTTP or HTTPS.
- Keep the app's host mapping bound to `127.0.0.1:3000` for host-local checks.
- Use Systems Manager for routine administration; temporary SSH should remain
  restricted as documented in `docs/ec2-runtime-bootstrap.md`.
- Store `CLOUDFLARE_TUNNEL_TOKEN` only as a GitHub Actions secret.

## First Deployment Validation

1. Confirm the EC2 bootstrap preflight has no failures.
2. Confirm the tunnel hostname is configured with `http://app:3000`.
3. Confirm `ORIGIN` is `https://cookbook.roadmap.links` in GitHub Actions
   variables.
4. Run the GitHub Actions `deploy` action with `stop_after_deploy` disabled.
5. On EC2 through Systems Manager, run:

   ```bash
   sudo APP_DIR=/opt/cookbook bash /opt/cookbook/scripts/verify-local-compose.sh
   ```

6. From a machine outside EC2, run:

   ```bash
   bash scripts/verify-cloudflare-route.sh cookbook.roadmap.links
   ```

7. Open `https://cookbook.roadmap.links` in a browser and complete or verify the
   Vanilla Cookbook first-run flow.
8. Confirm EC2 still has no inbound HTTP, HTTPS, or public port 3000 rule.

Continue with `docs/operations-runbook.md` for routine operation and
`docs/backup-restore.md` before storing important data.

## Troubleshooting

### Tunnel Token Missing

The `cloudflared` service may exit immediately or repeatedly restart. Confirm
the GitHub Actions secret is named exactly `CLOUDFLARE_TUNNEL_TOKEN`, then run a
new deployment. Do not print `.env`, inspect the container command, or paste the
token into logs while diagnosing it.

### Hostname Not Configured

DNS may not resolve, or Cloudflare may return a route error. In Zero Trust,
confirm the public hostname belongs to the correct tunnel and is exactly
`cookbook.roadmap.links`. In Cloudflare DNS, confirm the tunnel-managed proxied
record exists and there is no conflicting A, AAAA, or CNAME record.

### Compose Service Not Healthy

Run `scripts/verify-local-compose.sh` on EC2. If the app is not reachable on
`127.0.0.1:3000`, inspect app status before troubleshooting Cloudflare. Use
targeted logs carefully and never print `.env` or the full `cloudflared`
container command because it can contain the token.

### Wrong Service URL

If the local app works but Cloudflare reports an origin connection failure,
verify the tunnel service is `http://app:3000`. `http://localhost:3000` points
back into the `cloudflared` container and cannot reach the app service.

### App Origin Mismatch

Login, redirects, or browser requests can fail when Vanilla Cookbook's `ORIGIN`
does not match the public URL. Set the GitHub Actions variable `ORIGIN` to
`https://cookbook.roadmap.links`, deploy again so `.env` is rendered, and verify
the browser is using that exact scheme and hostname.
