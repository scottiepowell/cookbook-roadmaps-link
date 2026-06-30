import sqlite3

import pytest

from app.recipe_reader import NoRecipeTableFoundError, load_recipe_documents
from app.schema_inspector import inspect_schema


def create_fixture_db(path):
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
    connection.execute(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "Lemon Beans",
            "Bright pantry dinner",
            '["beans", "lemon", "olive oil"]',
            "Warm beans\nAdd lemon\nServe",
            "dinner\nvegetarian",
            "https://example.test/lemon-beans",
        ),
    )
    connection.execute(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (2, "Toast", None, None, None, None, None),
    )
    connection.commit()
    connection.close()


def test_schema_inspection_returns_tables_and_columns(tmp_path):
    db_path = tmp_path / "recipes.sqlite"
    create_fixture_db(db_path)

    schema = inspect_schema(db_path)

    assert [table.name for table in schema] == ["recipes"]
    recipe_columns = {column.name: column for column in schema[0].columns}
    assert set(recipe_columns) == {
        "id",
        "title",
        "description",
        "ingredients",
        "instructions",
        "tags",
        "source_url",
    }
    assert recipe_columns["id"].primary_key_position == 1
    assert recipe_columns["title"].nullable is False


def test_recipe_reader_returns_normalized_documents(tmp_path):
    db_path = tmp_path / "recipes.sqlite"
    create_fixture_db(db_path)

    recipes = load_recipe_documents(db_path)

    assert len(recipes) == 2
    first = recipes[0]
    assert first.id == "1"
    assert first.title == "Lemon Beans"
    assert first.description == "Bright pantry dinner"
    assert first.ingredients == ["beans", "lemon", "olive oil"]
    assert first.instructions == ["Warm beans", "Add lemon", "Serve"]
    assert first.tags == ["dinner", "vegetarian"]
    assert first.source == "https://example.test/lemon-beans"
    assert first.raw["title"] == "Lemon Beans"


def test_recipe_reader_uses_safe_defaults_for_missing_optional_fields(tmp_path):
    db_path = tmp_path / "recipes.sqlite"
    create_fixture_db(db_path)

    recipes = load_recipe_documents(db_path)
    second = recipes[1]

    assert second.id == "2"
    assert second.title == "Toast"
    assert second.description is None
    assert second.ingredients == []
    assert second.instructions == []
    assert second.tags == []
    assert second.source is None


def test_no_recipe_like_table_returns_controlled_error(tmp_path):
    db_path = tmp_path / "not_recipes.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
    connection.execute("INSERT INTO notes (body) VALUES ('not a recipe')")
    connection.commit()
    connection.close()

    with pytest.raises(NoRecipeTableFoundError, match="No recipe-like table"):
        load_recipe_documents(db_path)


def test_reader_opens_database_read_only(tmp_path):
    db_path = tmp_path / "recipes.sqlite"
    create_fixture_db(db_path)

    load_recipe_documents(db_path)

    connection = sqlite3.connect(db_path)
    count = connection.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    connection.close()
    assert count == 2
