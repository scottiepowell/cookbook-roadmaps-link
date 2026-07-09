from fastapi.testclient import TestClient

from app.demo_data import seed_demo_data
from app.main import app


def test_demo_ui_route_returns_html():
    response = TestClient(app).get("/demo")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Cookbook AI" in response.text
    assert "Structured Recipe Importer" in response.text
    assert "System and demo data" in response.text
    assert "Step 1" in response.text
    assert "Step 5" in response.text


def test_demo_ai_route_returns_same_html():
    response = TestClient(app).get("/demo/ai")

    assert response.status_code == 200
    assert "Dataset Ask/RAG" in response.text


def test_demo_static_assets_load():
    client = TestClient(app)

    css_response = client.get("/static/demo.css")
    js_response = client.get("/static/demo.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "fetch(" in js_response.text
    assert "importerAnswer" in js_response.text
    assert "importerEvidenceSection" in js_response.text
    assert "servings" in js_response.text
    assert "data.citations" in js_response.text
    assert "No importer citations were returned" in js_response.text
    assert "Retrieval metadata" in js_response.text


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
        client.get("/static/demo.css"),
        client.get("/static/demo.js"),
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
