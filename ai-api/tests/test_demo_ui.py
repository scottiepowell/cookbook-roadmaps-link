from fastapi.testclient import TestClient

from app.demo_data import seed_demo_data
from app.main import app


def test_demo_ui_route_returns_html():
    response = TestClient(app).get("/demo")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Cookbook AI" in response.text
    assert "Structured Recipe Importer" in response.text
    assert "Recipe Session Alpha" in response.text
    assert "process-only requirements flow" in response.text
    assert "Sessions expire" in response.text
    assert "Invite sessions, when enabled, use the X-AI-Demo-Session-Token header." in response.text
    assert "Local usage report" in response.text
    assert "Refresh usage report" in response.text
    assert "Start session" in response.text
    assert "Send follow-up" in response.text
    assert "Finalize for demo" in response.text
    assert "System and demo data" in response.text
    assert "Step 1" in response.text
    assert "Step 5" in response.text


def test_demo_ai_route_returns_same_html():
    response = TestClient(app).get("/demo/ai")

    assert response.status_code == 200
    assert "Dataset Ask/RAG" in response.text


def test_local_product_shell_connects_cookbook_and_ai_workflows():
    client = TestClient(app)
    response = client.get("/product")

    assert response.status_code == 200
    assert "Cookbook AI" in response.text
    assert "Vanilla Cookbook" in response.text
    assert "/product/cookbook" in response.text
    assert "/product/ai" in response.text
    assert "Recipe Creator" in response.text
    assert "Local/demo-only" in response.text
    assert "mock/offline by default" in response.text
    assert "never write production storage" in response.text
    assert "start-ai-demo-local.ps1" in response.text
    assert "Live OpenAI" in response.text
    assert "Mock offline" in response.text
    assert "gpt-5.4-nano" in response.text
    assert client.get("/product/ai", follow_redirects=False).headers["location"] == "/demo"
    assert client.get("/product/cookbook", follow_redirects=False).headers["location"] == "http://127.0.0.1:3000/"


def test_demo_static_assets_load():
    client = TestClient(app)

    css_response = client.get("/static/demo.css")
    js_response = client.get("/static/demo.js")
    product_js_response = client.get("/static/product.js")
    product_css_response = client.get("/static/product.css")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert product_js_response.status_code == 200
    assert product_css_response.status_code == 200
    for marker in ("box-sizing", "max-width", "grid-template-columns", "@media"):
        assert marker in product_css_response.text
    assert "Mock/offline default is active." in product_js_response.text
    assert "Fixtures are missing" in product_js_response.text
    assert "fetch(" in js_response.text
    assert "importerAnswer" in js_response.text
    assert "importerEvidenceSection" in js_response.text
    assert "renderRecipeSession" in js_response.text
    assert "/ai/recipe-session/start" in js_response.text
    assert "recipe-session-message" in js_response.text
    assert "recipe-session-finalize" in js_response.text
    assert "clarification_needed" in js_response.text
    assert "rag_refreshed" in js_response.text
    assert "draft_revised" in js_response.text
    assert "no_material_change" in js_response.text
    assert "ready_to_finalize" in js_response.text
    assert "last_citation_ids" in js_response.text
    assert "Clarification question" in js_response.text
    assert "No draft was generated because one clarification is needed." in js_response.text
    assert "Existing draft and citations were reused" in js_response.text
    assert "does not write to production storage" in js_response.text
    assert "Recipe session was not found or has expired." in js_response.text
    assert "Recoverable demo issue" in js_response.text
    assert "servings" in js_response.text
    assert "data.citations" in js_response.text
    assert "No importer citations were returned for this response." in js_response.text
    assert "No useful dataset examples were available for this response." in js_response.text
    assert "RAG support:" in js_response.text
    assert "Invite sessions" in js_response.text
    assert "support_level" in js_response.text
    assert "support_message" in js_response.text
    assert "usage-report-grid" in js_response.text
    assert "/ai/admin/usage-report" in js_response.text
    assert "formatUsd" in js_response.text
    assert "cache" in js_response.text
    assert "index_cache_hit" in js_response.text
    assert "entries" in js_response.text
    assert "Partial example" in js_response.text
    assert "Broad example" in js_response.text
    assert "Citation(s) returned" not in js_response.text
    assert "Retrieval metadata" in js_response.text
    assert "retrieved_examples" in js_response.text
    assert "Source ID:" in js_response.text
    assert "Provenance:" in js_response.text
    assert "Snippet:" in js_response.text
    assert "packed_examples" in js_response.text
    assert "packed_ids" in js_response.text
    assert "dropped_ids" in js_response.text
    assert "context_chars_used" in js_response.text
    assert "weak_examples_included" in js_response.text
    assert "context_budget_warning" in js_response.text
    assert "anchors:" in js_response.text
    assert "relevance:" in js_response.text
    assert "should_claim_rag_grounded" in js_response.text
    assert "should_show_weak_support_warning" in js_response.text
    assert "matched_ids:" in js_response.text
    assert "scores:" in js_response.text


def test_demo_readiness_endpoint_returns_safe_status():
    response = TestClient(app).get("/demo/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["service"]["ok"] is True
    assert "mode" in data["provider"]
    assert "available" in data["saved_recipes"]
    assert "available" in data["dataset"]
    assert "C:\\" not in response.text
    assert "/Users/" not in response.text


def test_seeded_demo_data_supports_saved_recipe_workflows(tmp_path, monkeypatch):
    paths = seed_demo_data(tmp_path)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(paths["db_path"]))
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(paths["dataset_dir"]))
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.delenv("AI_PROVIDER_CALLS_ENABLED", raising=False)
    monkeypatch.delenv("AI_PROVIDER_GLOBAL_DISABLE", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_BUDGET_MODE", raising=False)
    monkeypatch.delenv("AI_PROVIDER_BUDGET_SESSION_ID", raising=False)
    monkeypatch.delenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", raising=False)
    monkeypatch.delenv("AI_OPERATOR_GATE_TOKEN", raising=False)
    monkeypatch.delenv("AI_OPERATOR_GATE_ALLOWED_WORKFLOWS", raising=False)
    monkeypatch.delenv("AI_OPERATOR_GATE_LOCAL_BYPASS", raising=False)

    client = TestClient(app)

    readiness = client.get("/demo/readiness")
    assert readiness.status_code == 200
    readiness_data = readiness.json()
    assert readiness_data["saved_recipes"]["available"] is True
    assert readiness_data["saved_recipes"]["count"] >= 3
    assert "C:\\" not in readiness.text
    assert "/Users/" not in readiness.text

    ask_response = client.post("/ai/ask", json={"question": "What saved recipe uses lemon?", "limit": 2})
    assert ask_response.status_code == 200
    ask_data = ask_response.json()
    assert ask_data["citations"]
    assert any("Lemon" in citation["title"] for citation in ask_data["citations"])
    assert ask_data["provider"] == "mock"

    importer_response = client.post(
        "/ai/import-recipe",
        json={"text": "omelet with eggs cheese maybe onions cooked in butter fold it over", "source": "demo"},
    )
    assert importer_response.status_code == 200
    importer_data = importer_response.json()
    assert importer_data["citations"]
    assert importer_data["retrieval"]["retrieved_count"] >= 1

    meal_response = client.post(
        "/ai/meal-plan",
        json={"days": 1, "meals_per_day": 1, "preferences": "lemon dinner", "candidate_limit": 3},
    )
    assert meal_response.status_code == 200
    meal_data = meal_response.json()
    assert meal_data["selection"]["candidate_count"] >= 1
    assert meal_data["citations"]
    assert any("Lemon" in citation["title"] for citation in meal_data["citations"])


def test_demo_static_assets_do_not_include_sensitive_value_placeholders():
    client = TestClient(app)
    responses = [
        client.get("/demo"),
        client.get("/product"),
        client.get("/static/demo.css"),
        client.get("/static/demo.js"),
        client.get("/static/product.js"),
        client.get("/static/product.css"),
    ]
    forbidden = (
        "OPENAI_API_KEY",
        "sk-",
        "Authorization:",
        "CLOUDFLARE_TUNNEL_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
        ".env",
    )
    for response in responses:
        assert response.status_code == 200
        for marker in forbidden:
            assert marker not in response.text


def test_demo_ui_renders_recipe_session_requirement_diff_and_revision_summary():
    client = TestClient(app)
    script = client.get("/static/demo.js")

    assert script.status_code == 200
    assert "requirement_diff" in script.text
    assert "revision_summary" in script.text
    assert "Latest requirement change" in script.text
