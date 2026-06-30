import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import get_cookbook_db_path
from app.schema_inspector import TableInfo, inspect_schema, open_read_only_sqlite
from app.schemas import RecipeDocument


class RecipeReaderError(RuntimeError):
    """Raised when recipe documents cannot be read safely."""


class NoRecipeTableFoundError(RecipeReaderError):
    """Raised when no conservative recipe-like table exists."""


ID_COLUMN_CANDIDATES = ("id", "uuid", "slug")
TITLE_COLUMN_CANDIDATES = ("title", "name")
DESCRIPTION_COLUMN_CANDIDATES = ("description", "summary", "notes")
INGREDIENT_COLUMN_CANDIDATES = ("ingredients", "ingredient_text", "ingredient")
INSTRUCTION_COLUMN_CANDIDATES = ("instructions", "directions", "steps", "method")
TAG_COLUMN_CANDIDATES = ("tags", "categories", "category")
SOURCE_COLUMN_CANDIDATES = ("source", "source_url", "url", "link")


def load_recipe_documents(db_path: str | Path | None = None) -> list[RecipeDocument]:
    path = db_path or get_cookbook_db_path()
    schema = inspect_schema(path)
    recipe_table = _find_recipe_table(schema)
    if recipe_table is None:
        raise NoRecipeTableFoundError("No recipe-like table found in SQLite database.")

    with open_read_only_sqlite(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f'SELECT * FROM "{recipe_table.name}"').fetchall()

    columns = [column.name for column in recipe_table.columns]
    column_map = _map_columns(columns)

    return [_row_to_recipe_document(row, column_map) for row in rows]


def _find_recipe_table(schema: list[TableInfo]) -> TableInfo | None:
    for table in schema:
        column_names = {column.name.lower() for column in table.columns}
        has_title = any(candidate in column_names for candidate in TITLE_COLUMN_CANDIDATES)
        has_recipe_body = any(
            candidate in column_names
            for candidate in INGREDIENT_COLUMN_CANDIDATES + INSTRUCTION_COLUMN_CANDIDATES
        )
        table_name_matches = "recipe" in table.name.lower()
        if has_title and (has_recipe_body or table_name_matches):
            return table
    return None


def _map_columns(columns: list[str]) -> dict[str, str | None]:
    lower_to_original = {column.lower(): column for column in columns}
    return {
        "id": _first_present(lower_to_original, ID_COLUMN_CANDIDATES),
        "title": _first_present(lower_to_original, TITLE_COLUMN_CANDIDATES),
        "description": _first_present(lower_to_original, DESCRIPTION_COLUMN_CANDIDATES),
        "ingredients": _first_present(lower_to_original, INGREDIENT_COLUMN_CANDIDATES),
        "instructions": _first_present(lower_to_original, INSTRUCTION_COLUMN_CANDIDATES),
        "tags": _first_present(lower_to_original, TAG_COLUMN_CANDIDATES),
        "source": _first_present(lower_to_original, SOURCE_COLUMN_CANDIDATES),
    }


def _first_present(columns: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return columns[candidate]
    return None


def _row_to_recipe_document(row: sqlite3.Row, column_map: dict[str, str | None]) -> RecipeDocument:
    raw = dict(row)
    id_column = column_map["id"]
    title_column = column_map["title"]

    recipe_id = _string_value(raw.get(id_column)) if id_column else None
    title = _string_value(raw.get(title_column)) if title_column else None

    if not recipe_id:
        recipe_id = title or "unknown"
    if not title:
        title = f"Untitled recipe {recipe_id}"

    return RecipeDocument(
        id=recipe_id,
        title=title,
        description=_optional_string(raw, column_map["description"]),
        ingredients=_list_value(raw.get(column_map["ingredients"])) if column_map["ingredients"] else [],
        instructions=_list_value(raw.get(column_map["instructions"])) if column_map["instructions"] else [],
        tags=_list_value(raw.get(column_map["tags"])) if column_map["tags"] else [],
        source=_optional_string(raw, column_map["source"]),
        raw=raw,
    )


def _optional_string(raw: dict[str, Any], column: str | None) -> str | None:
    if not column:
        return None
    value = _string_value(raw.get(column))
    return value or None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [_string_value(item) for item in parsed if _string_value(item)]
        return [_string_value(part) for part in stripped.replace("\r\n", "\n").split("\n") if _string_value(part)]
    if isinstance(value, list):
        return [_string_value(item) for item in value if _string_value(item)]
    return [_string_value(value)]
