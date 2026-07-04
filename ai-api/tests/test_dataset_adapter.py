import json
import sqlite3

from app.dataset_adapter import inspect_recipe_dataset


def test_dataset_adapter_detects_expected_files_and_missing_warnings(tmp_path):
    inspection = inspect_recipe_dataset(tmp_path)

    assert len(inspection.files) == 6
    assert all(not status.present for status in inspection.files)
    assert "13k-recipes.csv is missing." in inspection.warnings
    assert inspection.csv is None
    assert inspection.sqlite == []
    assert inspection.metadata is None


def test_dataset_adapter_inspects_csv_schema_and_normalized_preview(tmp_path):
    csv_path = tmp_path / "13k-recipes.csv"
    csv_path.write_text(
        "Title,Ingredients,Instructions,Image_Name\n"
        "Lemon Beans,\"beans; lemon\",\"Warm beans\",lemon.jpg\n",
        encoding="utf-8",
    )

    inspection = inspect_recipe_dataset(tmp_path)

    assert inspection.csv is not None
    assert inspection.csv.columns == ["Title", "Ingredients", "Instructions", "Image_Name"]
    assert inspection.csv.row_count_previewed == 1
    assert inspection.normalized_preview is not None
    assert inspection.normalized_preview.title == "Lemon Beans"
    assert inspection.normalized_preview.ingredients == "beans; lemon"
    assert inspection.normalized_preview.instructions == "Warm beans"


def test_dataset_adapter_inspects_sqlite_schemas_read_only(tmp_path):
    db_path = tmp_path / "13k-recipes.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE recipes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    connection.execute("INSERT INTO recipes (title) VALUES ('Existing')")
    connection.commit()
    connection.close()

    inspection = inspect_recipe_dataset(tmp_path)

    assert len(inspection.sqlite) == 1
    assert inspection.sqlite[0].file_name == "13k-recipes.db"
    assert inspection.sqlite[0].tables[0].name == "recipes"
    assert [column.name for column in inspection.sqlite[0].tables[0].columns] == ["id", "title"]

    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, title FROM recipes").fetchall()
    connection.close()
    assert rows == [(1, "Existing")]


def test_dataset_adapter_inspects_metadata_json(tmp_path):
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps({"title": "Food Ingredients and Recipes Dataset with Images", "license": "CC BY-SA 3.0"}),
        encoding="utf-8",
    )

    inspection = inspect_recipe_dataset(tmp_path)

    assert inspection.metadata is not None
    assert inspection.metadata.keys == ["license", "title"]
    assert inspection.metadata.values["license"] == "CC BY-SA 3.0"
