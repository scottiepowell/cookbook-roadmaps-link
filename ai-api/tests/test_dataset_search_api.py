from fastapi.testclient import TestClient

from app.main import app


def test_get_dataset_search_returns_ranked_fixture_results(tmp_path, monkeypatch):
    (tmp_path / "13k-recipes.csv").write_text(
        ",Title,Ingredients,Instructions,Image_Name,Cleaned_Ingredients\n"
        "10,Lemon Beans,\"beans; lemon\",\"Warm beans\",lemon.jpg,\"beans; lemon\"\n"
        "11,Bean Stew,carrot,\"Add beans and lemon\",stew.jpg,carrot\n"
        "12,Pasta Bowl,beans,\"Boil pasta\",pasta.jpg,beans\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).get("/dataset/search", params={"q": "beans", "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "beans"
    assert data["count"] == 3
    assert [result["source_id"] for result in data["results"]] == ["10", "11", "12"]
    assert data["results"][0]["matched_fields"] == ["title", "ingredients", "instructions"]
    assert data["results"][0]["provenance"]["license"] == "CC BY-SA 3.0"
    assert data["results"][0]["provenance"]["source_file"] == "13k-recipes.csv"
    assert data["index"]["document_count"] == 3
    assert data["index"]["source_counts"] == {"13k-recipes.csv": 3}
    assert "ingredients" in data["index"]["fields_indexed"]
    assert data["results"][0]["snippet"] == "Lemon Beans"


def test_post_dataset_search_works_with_fixture_data(tmp_path, monkeypatch):
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "abc,Lentil Soup,\"lentils; onion\",\"Simmer soup\",middle eastern\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).post("/dataset/search", json={"query": "middle", "limit": 5, "dataset_limit": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["source_id"] == "abc"
    assert data["results"][0]["matched_fields"] == ["tags"]
    assert data["index"]["build_metadata"]["record_limit"] == 1
    assert data["index"]["build_metadata"]["dataset_dir"] == "configured"


def test_dataset_search_empty_query_returns_summary_without_results(tmp_path, monkeypatch):
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions\nabc,Lentil Soup,lentils,Simmer\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).get("/dataset/search", params={"q": ""})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []
    assert data["index"]["document_count"] == 1


def test_dataset_search_missing_dataset_returns_controlled_warning(tmp_path, monkeypatch):
    missing_dir = tmp_path / "missing"
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(missing_dir))

    response = TestClient(app).get("/dataset/search", params={"q": "beans"})

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []
    assert data["index"]["document_count"] == 0
    assert "Configured recipe dataset directory does not exist." in data["warnings"]
    assert str(missing_dir) not in str(data)


def test_dataset_search_does_not_create_index_artifacts(tmp_path, monkeypatch):
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions\nabc,Lentil Soup,lentils,Simmer\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).get("/dataset/search", params={"q": "lentils"})

    assert response.status_code == 200
    assert not list(tmp_path.glob("*.index"))
    assert not list(tmp_path.glob("*.idx"))
