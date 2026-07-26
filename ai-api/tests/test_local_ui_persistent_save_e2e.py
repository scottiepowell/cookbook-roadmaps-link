from pathlib import Path


def script_text() -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / "scripts" / "test-local-ui-persistent-save-e2e.ps1").read_text(encoding="utf-8")


def test_local_e2e_script_requires_explicit_approval_and_exact_local_runtime():
    script = script_text()

    assert "ApproveLocalWrite" in script
    assert "local/vanilla-cookbook-adapter:0034g" in script
    assert "cookbook-local" in script
    assert "http://127.0.0.1:3000/" in script
    assert "RUN_LOCAL_PERSISTENT_AUTH_FIXTURE" in script
    assert "SYNTHETIC_AUTH_FIXTURE" in script
    assert "AI_LOCAL_SAVE_ENABLED" in script
    assert "AI_LOCAL_SAVE_APPROVED" in script
    assert "uvicorn" in script
    assert "0034i-e2e" in script


def test_local_e2e_script_exercises_mock_import_dry_run_confirmation_and_safe_result():
    script = script_text()

    assert 'AI_PROVIDER = "mock"' in script
    assert "/ai/import-recipe" in script
    assert "/adapter/recipes/import-candidate/dry-run" in script
    assert "/adapter/recipes/import-candidate/local-persistent-commit" in script
    assert "confirm_local_save=$true" in script
    assert "recipe_uid" in script
    assert "read_after_write" in script
    assert "browser observation is not attempted" in script


def test_local_e2e_script_has_cleanup_and_rejects_sensitive_or_deployment_contexts():
    script = script_text()

    assert "finally" in script
    assert "stop-vanilla-cookbook-local.ps1" in script
    assert "Remove-Item -LiteralPath $path" in script
    for marker in ("GITHUB_ACTIONS", "CLOUDFLARE_TUNNEL_TOKEN", "TUNNEL_TOKEN", "AWS_REGION"):
        assert marker in script
    for forbidden in ("OPENAI_API_KEY", "oauth_code", "provider_token", "storage_grant"):
        assert forbidden.lower() not in script.lower()
