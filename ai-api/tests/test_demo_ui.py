from fastapi.testclient import TestClient

from app.main import app


def test_demo_ui_route_returns_html():
    response = TestClient(app).get("/demo")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Cookbook AI" in response.text
    assert "Structured Recipe Importer" in response.text


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


def test_demo_html_does_not_include_sensitive_value_placeholders():
    response = TestClient(app).get("/demo")

    forbidden = (
        "OPENAI_API_KEY",
        "sk-",
        "Authorization:",
        "CLOUDFLARE_TUNNEL_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
    )
    for marker in forbidden:
        assert marker not in response.text
