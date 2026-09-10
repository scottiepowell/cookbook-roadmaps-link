from pathlib import Path


def test_git_bash_public_stack_launcher_has_safe_startup_contract():
    script = (Path(__file__).parents[2] / "scripts" / "start-public-cookbook.sh").read_text()

    assert "docker info" in script
    assert "Docker Desktop.exe" in script
    assert "docker compose -f \"$COMPOSE_FILE\" config --quiet" in script
    assert "docker compose -f \"$COMPOSE_FILE\" up -d" in script
    assert "PUBLIC_CORE_ENV_FILE" in script
    assert "PUBLIC_CORE_OIDC_ENV_FILE" in script
    assert "cookbook-public-cloudflared" in script
    assert "dockerInference" in script
    assert "restart WslService as Administrator" in script
    assert "cat .env" not in script
    assert "set -x" not in script
