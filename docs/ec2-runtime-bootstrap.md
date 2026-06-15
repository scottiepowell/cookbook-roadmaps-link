# EC2 Runtime Bootstrap

This is the manual preparation path for the Ubuntu EC2 host used by Vanilla
Cookbook. It installs host dependencies and validates the machine before the
GitHub Actions deployment workflow is used. It does not create AWS resources or
write application secrets.

## Recommended EC2 Settings

- Use a current Ubuntu Server LTS AMI.
- Choose a small instance type that is Free Tier eligible for the account and
  region when possible. Eligibility and pricing vary, so confirm them in AWS
  before launch.
- Use an EBS-backed, encrypted root volume sized for Docker images, uploads,
  database data, and backups. Stop/start then preserves this host data.
- Do not assign broad IAM permissions to the instance.

## Network And Access

The security group should not allow inbound HTTP or HTTPS. Cloudflare Tunnel
will make an outbound connection and publish the application without exposing
the EC2 web port.

Routine administration should use Systems Manager rather than SSH. If SSH is
needed for initial setup, allow TCP port 22 temporarily from only the operator's
current public IP, then remove that rule after Systems Manager is working. The
instance needs outbound HTTPS access to AWS Systems Manager endpoints, GitHub,
Docker registries, and Cloudflare.

Attach an instance profile containing `AmazonSSMManagedInstanceCore` or an
equivalent least-privilege policy. This instance profile is separate from the
GitHub OIDC workflow role.

## Run The Bootstrap

Place this repository on the host temporarily or transfer the reviewed script,
then run it as root:

```bash
sudo RUNTIME_USER=ubuntu bash scripts/bootstrap-ec2-runtime.sh
```

The script installs or verifies Git, curl, CA certificates, Ubuntu's Docker
package, Docker Compose, and AWS SSM Agent. It enables Docker and SSM, adds the
runtime user to the `docker` group, and creates `/opt/cookbook`. Log out and back
in after the first run so group membership is refreshed.

`RUNTIME_USER` must identify an existing non-root account. When omitted, the
script uses the invoking `sudo` user or the standard Ubuntu `ubuntu` user.
`APP_DIR` can override `/opt/cookbook`, but it must match the later GitHub
Actions variable. The script is idempotent and does not create `.env`.

## Run Preflight

Run preflight as root so it can accurately test the runtime user's directory
access and service states:

```bash
sudo RUNTIME_USER=ubuntu bash scripts/preflight-ec2-runtime.sh
```

The script reports operating system and user details, Git, Docker, Compose,
Docker and SSM service state, `/opt/cookbook` access, outbound HTTPS, and whether
port 3000 is listening. Warnings such as port 3000 not listening before the
first deployment do not fail preflight. Missing runtime requirements produce a
nonzero result and should be corrected before deployment.

## Connect GitHub Actions

Set these non-sensitive repository variables to the created instance:

```text
AWS_REGION=<instance region>
EC2_INSTANCE_ID=<instance ID>
APP_DIR=/opt/cookbook
```

Complete all other items in `docs/github-settings-checklist.md`, then run the
manual workflow in the documented order.

## Cloudflare And Cost Control

Later, create a Cloudflare Tunnel public hostname for
`cookbook.roadmaps.link` that routes to `http://app:3000`, and store its token
only as the corresponding GitHub Actions secret. Do not open EC2 inbound web
ports for the tunnel.

Use `docs/cloudflare-tunnel-setup.md` for dashboard and DNS steps. After the
first deployment, run `scripts/verify-local-compose.sh` on EC2 and
`scripts/verify-cloudflare-route.sh` from an external machine.

Stop the instance when the lab is not in use. Stopping avoids EC2 compute usage,
but EBS volumes, snapshots, Elastic IP addresses, and other retained resources
can continue to incur charges.
