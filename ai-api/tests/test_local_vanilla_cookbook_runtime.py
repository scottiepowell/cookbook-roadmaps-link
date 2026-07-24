from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.local.yml"
START = ROOT / "scripts" / "start-vanilla-cookbook-local.ps1"
STOP = ROOT / "scripts" / "stop-vanilla-cookbook-local.ps1"
CHECK = ROOT / "scripts" / "check-vanilla-cookbook-local.ps1"


def test_local_compose_is_local_app_only_and_has_disposable_mounts():
    text = COMPOSE.read_text(encoding="utf-8")

    assert "services:" in text
    assert "app:" in text
    assert "jt196/vanilla-cookbook:stable" in text
    assert '"127.0.0.1:3000:3000"' in text
    assert "./.local/vanilla-cookbook/db:/app/prisma/db" in text
    assert "./.local/vanilla-cookbook/uploads:/app/uploads" in text
    assert "cloudflared" not in text
    assert "CLOUDFLARE_TUNNEL_TOKEN" not in text
    assert "env_file" not in text


def test_local_runtime_scripts_use_local_compose_without_cloudflare_or_secrets():
    for path in (START, STOP, CHECK):
        text = path.read_text(encoding="utf-8")
        assert "docker-compose.local.yml" in text
        assert "cookbook-local" in text
        assert "docker info" in text
        assert "127.0.0.1:3000" in text or path == STOP
        assert "cloudflared" not in text.lower()
        assert "CLOUDFLARE_TUNNEL_TOKEN" not in text
        assert "OPENAI_API_KEY" not in text
        assert "env_file" not in text


def test_local_runtime_data_is_ignored_and_start_stop_commands_are_documented():
    ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert ".local/" in ignore_rules
    assert "start-vanilla-cookbook-local.ps1" in readme
    assert "stop-vanilla-cookbook-local.ps1" in readme
