import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def create_search_fixture_db(path):
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT,
            tags TEXT,
            source_url TEXT
        )
        """
    )
    rows = [
        (
            1,
            "Lemon Beans",
            "Bright pantry dinner",
            '["beans", "lemon", "olive oil"]',
            "Warm beans\nAdd lemon\nServe",
            "dinner\nvegetarian",
            "https://example.test/lemon-beans",
        ),
        (
            2,
            "Bean Salad",
            "Cold lunch",
            '["white beans", "cucumber", "parsley"]',
            "Chop vegetables\nToss with beans",
            "lunch",
            None,
        ),
        (
            3,
            "Pasta Bake",
            None,
            '["pasta", "tomato", "cheese"]',
            "Boil pasta\nBake with cheese",
            "dinner",
            None,
        ),
    ]
    connection.executemany(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()
    connection.close()


def test_get_recipe_search_uses_cookbook_db_path_fixture(tmp_path, monkeypatch):
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "OLLAMA_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    db_path = tmp_path / "recipes.sqlite"
    create_search_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).get("/recipes/search", params={"q": "cucumber", "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "cucumber"
    assert data["count"] == 1
    assert data["results"][0]["id"] == "2"
    assert data["results"][0]["matched_fields"] == ["ingredients"]
    assert "ingredients" in data["results"][0]["matched_fields"]
    assert "raw" not in data["results"][0]


def test_post_recipe_search_works(tmp_path, monkeypatch):
    db_path = tmp_path / "recipes.sqlite"
    create_search_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post("/recipes/search", json={"query": "vegetarian", "limit": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == "1"
    assert data["results"][0]["matched_fields"] == ["tags"]


def test_search_endpoint_returns_empty_for_no_match(tmp_path, monkeypatch):
    db_path = tmp_path / "recipes.sqlite"
    create_search_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).get("/recipes/search", params={"q": "chocolate"})

    assert response.status_code == 200
    assert response.json() == {"query": "chocolate", "count": 0, "results": []}


def test_search_endpoint_returns_empty_for_empty_query(tmp_path, monkeypatch):
    db_path = tmp_path / "recipes.sqlite"
    create_search_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).get("/recipes/search", params={"q": ""})

    assert response.status_code == 200
    assert response.json() == {"query": "", "count": 0, "results": []}


def test_search_endpoint_returns_controlled_error_for_missing_recipe_table(tmp_path, monkeypatch):
    db_path = tmp_path / "notes.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
    connection.execute("INSERT INTO notes (body) VALUES ('not a recipe')")
    connection.commit()
    connection.close()
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).get("/recipes/search", params={"q": "anything"})

    assert response.status_code == 422
    assert "No recipe-like table" in response.json()["detail"]
