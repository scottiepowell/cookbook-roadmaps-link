import sqlite3

from app.dataset_adapter import ExternalRecipeRecord, iter_recipe_dataset_records
from app.dataset_index import build_index_from_dataset, build_recipe_index, search_recipe_index


def test_dataset_record_reader_streams_bounded_csv_records(tmp_path):
    (tmp_path / "13k-recipes.csv").write_text(
        ",Title,Ingredients,Instructions,Image_Name,Cleaned_Ingredients\n"
        "10,Lemon Beans,\"beans; lemon\",\"Warm beans\",lemon.jpg,\"beans; lemon\"\n"
        "11,Apple Salad,\"apple; mint\",\"Toss salad\",apple.jpg,\"apple; mint\"\n",
        encoding="utf-8",
    )

    records = iter_recipe_dataset_records(tmp_path, limit=1)

    assert len(records) == 1
    assert records[0].source_id == "10"
    assert records[0].title == "Lemon Beans"
    assert records[0].ingredients == ["beans", "lemon"]
    assert records[0].instructions == ["Warm beans"]
    assert records[0].source_file == "13k-recipes.csv"


def test_dataset_record_reader_streams_sqlite_records_read_only(tmp_path):
    db_path = tmp_path / "13k-recipes.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE recipes (id INTEGER PRIMARY KEY, name TEXT NOT NULL, ingredients TEXT, directions TEXT, category TEXT)"
    )
    connection.execute(
        "INSERT INTO recipes (id, name, ingredients, directions, category) VALUES (7, 'Tomato Pasta', 'tomato; pasta', 'Boil pasta', 'dinner')"
    )
    connection.commit()
    connection.close()

    records = iter_recipe_dataset_records(tmp_path, limit=5)

    assert len(records) == 1
    assert records[0].source_id == "7"
    assert records[0].title == "Tomato Pasta"
    assert records[0].tags == ["dinner"]
    assert records[0].source_file == "13k-recipes.db"
    assert records[0].source_table == "recipes"

    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, name FROM recipes").fetchall()
    connection.close()
    assert rows == [(7, "Tomato Pasta")]


def test_recipe_index_summary_and_deterministic_ranking():
    index = build_recipe_index(
        [
            ExternalRecipeRecord(
                source_id="1",
                title="Lemon Beans",
                ingredients=["beans", "lemon"],
                instructions=["Simmer until warm"],
                tags=["dinner"],
                source_file="13k-recipes.csv",
            ),
            ExternalRecipeRecord(
                source_id="2",
                title="Bean Stew",
                ingredients=["carrot"],
                instructions=["Add lemon and beans"],
                tags=[],
                source_file="13k-recipes.csv",
            ),
            ExternalRecipeRecord(
                source_id="3",
                title="Pasta Bowl",
                ingredients=["beans"],
                instructions=["Serve with lemon"],
                tags=[],
                source_file="5k-recipes.db",
                source_table="recipes",
            ),
        ]
    )

    assert index.summary.document_count == 3
    assert index.summary.source_counts == {"13k-recipes.csv": 2, "5k-recipes.db": 1}
    assert index.summary.fields_indexed == ["title", "tags", "ingredients", "instructions", "source"]
    assert index.summary.token_count > 0
    assert index.summary.build_metadata == {"mode": "in_memory", "input_records": 3}
    assert index.summary.warnings == []
    assert index.documents[0].normalized_fields["title"] == "lemon beans"
    assert index.documents[0].normalized_field_tokens["ingredients"] == ["bean", "lemon"]
    assert index.documents[0].normalized_field_phrases["title"] == []

    results = search_recipe_index(index, "beans", limit=10)

    assert [result.source_id for result in results] == ["1", "2", "3"]
    assert results[0].matched_fields == ["title", "ingredients"]
    assert results[2].matched_fields == ["ingredients"]
    assert results[0].snippet == "Lemon Beans"


def test_recipe_index_search_handles_empty_and_no_match_queries():
    index = build_recipe_index(
        [
            ExternalRecipeRecord(
                source_id="1",
                title="Lemon Beans",
                ingredients=["beans"],
                instructions=[],
                tags=[],
                source_file="13k-recipes.csv",
            )
        ]
    )

    assert search_recipe_index(index, "", limit=10) == []
    assert search_recipe_index(index, "chocolate", limit=10) == []
    assert search_recipe_index(index, "beans", limit=0) == []


def test_build_index_from_dataset_uses_generated_fixture_without_artifacts(tmp_path):
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "abc,Lentil Soup,\"lentils; onion\",\"Simmer soup\",middle eastern\n",
        encoding="utf-8",
    )

    index = build_index_from_dataset(str(tmp_path), limit=20)
    results = search_recipe_index(index, "lentils", limit=5)

    assert index.summary.document_count == 1
    assert results[0].id == "13k-recipes.csv:abc"
    assert results[0].matched_fields == ["title", "ingredients"]
    assert not list(tmp_path.glob("*.index"))
