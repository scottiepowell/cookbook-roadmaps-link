# 0035L Git Bash Public Stack Launcher

Add a Windows Git Bash entry point that starts Docker Desktop when necessary
and brings up the existing public Cookbook core, AI sidecar, and provisioned
Cloudflare connector without printing private configuration.

The launcher must wait for Docker, validate ignored core env files, ensure the
named external network and volumes, run the existing public Compose file, start
the existing tunnel container when present, and report bounded health/status.
It must not create credentials, print env contents, run provider calls, mutate
recipes, or replace the existing Compose/deployment ownership boundaries.
