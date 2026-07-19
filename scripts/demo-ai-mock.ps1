Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$RunInviteSmoke = $env:AI_INVITE_SMOKE_ENABLED -eq "true"

$env:AI_PROVIDER = "mock"
$env:AI_OPERATOR_GATE_ENABLED = "false"
$env:AI_INVITE_SESSIONS_ENABLED = "false"
$env:AI_PROVIDER_CALLS_ENABLED = "true"
$env:AI_PROVIDER_GLOBAL_DISABLE = "false"
Remove-Item Env:AI_OPERATOR_GATE_TOKEN_FINGERPRINT -ErrorAction SilentlyContinue
Remove-Item Env:AI_OPERATOR_GATE_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:AI_OPERATOR_GATE_ALLOWED_WORKFLOWS -ErrorAction SilentlyContinue
Remove-Item Env:AI_OPERATOR_GATE_LOCAL_BYPASS -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_SESSION_TTL_SECONDS -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_GRANT_TTL_SECONDS -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_MAX_SESSIONS_PER_GRANT -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_ALLOWED_WORKFLOWS -ErrorAction SilentlyContinue
Remove-Item Env:AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_BUDGET_MODE -ErrorAction SilentlyContinue
Remove-Item Env:AI_PROVIDER_BUDGET_SESSION_ID -ErrorAction SilentlyContinue

Write-Host "AI demo mock path: offline evals"
& $Python "evals\ai_cookbook\run_evals.py"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "AI demo mock path: direct endpoint smoke"
$DemoPython = @'
import os
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, "ai-api")

from app.demo_data import seed_demo_data
from app.recipe_session import default_recipe_session_store
from fastapi.testclient import TestClient

from app.main import app


tmp_parent = Path(".tmp-ai-demo")
tmp_parent.mkdir(exist_ok=True)
tmp = tmp_parent / f"run-{uuid.uuid4().hex}"
tmp.mkdir()

try:
    root = tmp
    paths = seed_demo_data(root)
    os.environ["COOKBOOK_DB_PATH"] = str(paths["db_path"])
    os.environ["RECIPE_DATASET_DIR"] = str(paths["dataset_dir"])
    os.environ["AI_PROVIDER"] = "mock"
    os.environ["AI_OPERATOR_GATE_ENABLED"] = "false"
    os.environ["AI_INVITE_SESSIONS_ENABLED"] = "false"
    os.environ["AI_PROVIDER_CALLS_ENABLED"] = "true"
    os.environ["AI_PROVIDER_GLOBAL_DISABLE"] = "false"
    os.environ.pop("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", None)
    os.environ.pop("AI_OPERATOR_GATE_TOKEN", None)
    os.environ.pop("AI_OPERATOR_GATE_ALLOWED_WORKFLOWS", None)
    os.environ.pop("AI_OPERATOR_GATE_LOCAL_BYPASS", None)
    os.environ.pop("AI_INVITE_SESSION_TTL_SECONDS", None)
    os.environ.pop("AI_INVITE_GRANT_TTL_SECONDS", None)
    os.environ.pop("AI_INVITE_MAX_SESSIONS_PER_GRANT", None)
    os.environ.pop("AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS", None)
    os.environ.pop("AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD", None)
    os.environ.pop("AI_INVITE_ALLOWED_WORKFLOWS", None)
    os.environ.pop("AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED", None)
    os.environ.pop("AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION", None)
    os.environ.pop("AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL", None)
    os.environ.pop("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL", None)
    os.environ.pop("AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL", None)
    os.environ.pop("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION", None)
    os.environ.pop("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL", None)
    os.environ.pop("AI_PROVIDER_BUDGET_MODE", None)
    os.environ.pop("AI_PROVIDER_BUDGET_SESSION_ID", None)
    default_recipe_session_store.clear()

    client = TestClient(app)
    checks = [
        ("local_product", client.get("/product")),
        ("health", client.get("/health")),
        ("config", client.get("/ai/config")),
        ("usage_report", client.get("/ai/admin/usage-report")),
        ("importer", client.post("/ai/import-recipe", json={"text": "Lemon beans: warm beans with lemon.", "source": "demo", "provider_mode": "mock", "model": "mock-basic"})),
        ("ask_my_cookbook", client.post("/ai/ask", json={"question": "What uses lemon?", "limit": 1, "provider_mode": "mock", "model": "mock-basic"})),
        ("dataset_search", client.get("/dataset/search", params={"q": "tomato pasta", "limit": 1, "dataset_limit": 3})),
        ("dataset_ask", client.post("/dataset/ask", json={"question": "What indexed recipe uses tomato pasta?", "limit": 1, "dataset_limit": 3, "provider_mode": "mock", "model": "mock-basic"})),
        ("meal_plan", client.post("/ai/meal-plan", json={"days": 1, "meals_per_day": 1, "preferences": "lemon", "candidate_limit": 2, "provider_mode": "mock", "model": "mock-basic"})),
    ]

    for name, response in checks:
        if response.status_code != 200:
            raise SystemExit(f"{name} failed with HTTP {response.status_code}: {response.text}")
        text = response.text
        for forbidden in ("OPENAI_API_KEY", "sk-", "Authorization:"):
            if forbidden in text:
                raise SystemExit(f"{name} leaked forbidden text: {forbidden}")
        if name in {"importer", "ask_my_cookbook", "dataset_ask", "meal_plan"}:
            data = response.json()
            if data.get("provider") != "mock" or data.get("model") != "mock-basic":
                raise SystemExit(f"{name} did not honor explicit mock provider preference: {response.text}")
        print(f"PASS: {name}")

    product = client.get("/product")
    for required in ("Local integrated product", "Vanilla Cookbook", "Recipe Creator", "/product/cookbook", "/product/ai", "mock/offline by default", "never write production storage"):
        if required not in product.text:
            raise SystemExit(f"local_product missing expected integration marker: {required}")
    cookbook_redirect = client.get("/product/cookbook", follow_redirects=False)
    ai_redirect = client.get("/product/ai", follow_redirects=False)
    if cookbook_redirect.status_code not in (302, 307) or cookbook_redirect.headers.get("location") != "http://127.0.0.1:3000/":
        raise SystemExit("local_product cookbook redirect did not target the local upstream app")
    if ai_redirect.status_code not in (302, 307) or ai_redirect.headers.get("location") != "/demo":
        raise SystemExit("local_product AI redirect did not target the AI workspace")
    readiness = client.get("/demo/readiness")
    if readiness.status_code != 200:
        raise SystemExit(f"local_product readiness failed with HTTP {readiness.status_code}")
    for forbidden in ("OPENAI_API_KEY", "sk-", "Authorization:", "C:\\"):
        if forbidden in readiness.text or forbidden in product.text:
            raise SystemExit(f"local_product leaked forbidden text: {forbidden}")

    session_start = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight", "provider_mode": "mock", "model": "mock-basic"},
    )
    if session_start.status_code != 200:
        raise SystemExit(f"recipe_session_start failed with HTTP {session_start.status_code}: {session_start.text}")
    session_data = session_start.json()
    if session_data.get("response_state") != "draft_generated" or not session_data.get("interaction_id"):
        raise SystemExit(f"recipe_session_start returned unexpected state: {session_start.text}")
    if session_data.get("provider") != "mock" or session_data.get("model") != "mock-basic":
        raise SystemExit(f"recipe_session_start did not honor explicit mock provider preference: {session_start.text}")
    interaction_id = session_data["interaction_id"]
    print("PASS: recipe_session_start")

    session_message = client.post(
        f"/ai/recipe-session/{interaction_id}/message",
        json={"text": "actually make it no-bake", "provider_mode": "mock", "model": "mock-basic"},
    )
    if session_message.status_code != 200:
        raise SystemExit(f"recipe_session_message failed with HTTP {session_message.status_code}: {session_message.text}")
    message_data = session_message.json()
    if message_data.get("response_state") not in ("rag_refreshed", "draft_revised") or message_data.get("rag_refreshed") is not True:
        raise SystemExit(f"recipe_session_message returned unexpected state: {session_message.text}")
    if message_data.get("provider") != "mock" or message_data.get("model") != "mock-basic":
        raise SystemExit(f"recipe_session_message did not honor explicit mock provider preference: {session_message.text}")
    print("PASS: recipe_session_message")

    session_get = client.get(f"/ai/recipe-session/{interaction_id}")
    if session_get.status_code != 200:
        raise SystemExit(f"recipe_session_get failed with HTTP {session_get.status_code}: {session_get.text}")
    print("PASS: recipe_session_get")

    session_finalize = client.post(f"/ai/recipe-session/{interaction_id}/finalize", json={"format": "draft_json"})
    if session_finalize.status_code != 200 or session_finalize.json().get("response_state") != "ready_to_finalize":
        raise SystemExit(f"recipe_session_finalize returned unexpected state: {session_finalize.text}")
    print("PASS: recipe_session_finalize")

    vague = client.post("/ai/recipe-session/start", json={"text": "make dessert"})
    if vague.status_code != 200 or vague.json().get("response_state") != "clarification_needed":
        raise SystemExit(f"recipe_session_clarification returned unexpected state: {vague.text}")
    print("PASS: recipe_session_clarification")

    chatter = client.post(f"/ai/recipe-session/{interaction_id}/message", json={"text": "thanks"})
    if chatter.status_code != 200:
        raise SystemExit(f"recipe_session_chatter failed with HTTP {chatter.status_code}: {chatter.text}")
    chatter_data = chatter.json()
    if chatter_data.get("response_state") != "no_material_change" or chatter_data.get("rag_refreshed") is not False:
        raise SystemExit(f"recipe_session_chatter returned unexpected state: {chatter.text}")
    print("PASS: recipe_session_chatter")

    for name, response in (
        ("recipe_session_start", session_start),
        ("recipe_session_message", session_message),
        ("recipe_session_get", session_get),
        ("recipe_session_finalize", session_finalize),
        ("recipe_session_clarification", vague),
        ("recipe_session_chatter", chatter),
    ):
        for forbidden in ("OPENAI_API_KEY", "sk-", "Authorization:", "Traceback", ".tmp-ai-demo"):
            if forbidden in response.text:
                raise SystemExit(f"{name} leaked forbidden text: {forbidden}")

    if os.getenv("AI_INVITE_SMOKE_ENABLED", "false").lower() == "true":
        invite_grant = client.post(
            "/ai/invite/grants",
            json={
                "allowed_workflows": ["importer"],
                "max_sessions": 1,
                "max_provider_calls": 1,
                "max_estimated_cost_usd": "0.10",
                "notes": "Mock invite smoke",
                "operator_label": "mock-smoke",
            },
        )
        if invite_grant.status_code != 200:
            raise SystemExit(f"invite grant smoke failed with HTTP {invite_grant.status_code}: {invite_grant.text}")
        invite_data = invite_grant.json()
        invite_token = invite_data["invite_token"]
        invite_session = client.post("/ai/invite/redeem", json={"invite_token": invite_token})
        if invite_session.status_code != 200:
            raise SystemExit(f"invite redeem smoke failed with HTTP {invite_session.status_code}: {invite_session.text}")
        session_token = invite_session.json()["session_token"]
        invite_import = client.post(
            "/ai/import-recipe",
            headers={"X-AI-Demo-Session-Token": session_token},
            json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
        )
        if invite_import.status_code != 200:
            raise SystemExit(f"invite import smoke failed with HTTP {invite_import.status_code}: {invite_import.text}")
        revoked = client.post(f"/ai/invite/sessions/{invite_session.json()['session']['session_id']}/revoke")
        if revoked.status_code != 200:
            raise SystemExit(f"invite revoke smoke failed with HTTP {revoked.status_code}: {revoked.text}")
        blocked = client.post(
            "/ai/import-recipe",
            headers={"X-AI-Demo-Session-Token": session_token},
            json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
        )
        if blocked.status_code == 200:
            raise SystemExit("invite revoke smoke expected protected workflow to be blocked")
        print("PASS: invite_smoke")
finally:
    default_recipe_session_store.clear()
    shutil.rmtree(root, ignore_errors=True)
    try:
        tmp_parent.rmdir()
    except OSError:
        pass

print("Mock endpoint demo checks passed.")
'@

$DemoPython | & $Python -
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Mock AI demo checks passed."
