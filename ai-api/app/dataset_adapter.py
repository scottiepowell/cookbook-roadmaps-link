import csv
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import get_recipe_dataset_dir
from app.schema_inspector import TableInfo, inspect_schema, open_read_only_sqlite


EXPECTED_FILES = (
    "13k-recipes.csv",
    "13k-recipes.db",
    "5k-recipes.db",
    "metadata.json",
    "README.md",
    "tutorial.md",
)

ID_FIELDS = ("id", "recipe_id", "source_id", "index", "unnamed: 0", "")
TITLE_FIELDS = ("title", "name", "recipe_name")
INGREDIENT_FIELDS = ("ingredients", "cleaned_ingredients", "ingredient")
INSTRUCTION_FIELDS = ("instructions", "directions", "steps", "method")
TAG_FIELDS = ("tags", "tag", "category", "categories", "cuisine")


@dataclass(frozen=True)
class DatasetFileStatus:
    name: str
    path: str
    present: bool
    readable: bool
    size_bytes: int | None = None
    modified_ns: int | None = None
    warning: str | None = None


@dataclass(frozen=True)
class CsvSchemaPreview:
    file_name: str
    columns: list[str]
    sample_rows: list[dict[str, str]]
    row_count_previewed: int


@dataclass(frozen=True)
class SQLiteSchemaPreview:
    file_name: str
    tables: list[TableInfo]


@dataclass(frozen=True)
class MetadataPreview:
    file_name: str
    keys: list[str]
    values: dict[str, Any]


@dataclass(frozen=True)
class NormalizedRecipePreview:
    title: str | None
    ingredients: str | None
    instructions: str | None
    source_file: str


@dataclass(frozen=True)
class ExternalRecipeRecord:
    source_id: str
    title: str
    ingredients: list[str]
    instructions: list[str]
    tags: list[str]
    source_file: str
    source_table: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetInspection:
    dataset_dir: str
    files: list[DatasetFileStatus]
    csv: CsvSchemaPreview | None = None
    sqlite: list[SQLiteSchemaPreview] = field(default_factory=list)
    metadata: MetadataPreview | None = None
    normalized_preview: NormalizedRecipePreview | None = None
    warnings: list[str] = field(default_factory=list)


def inspect_recipe_dataset(dataset_dir: str | Path | None = None) -> DatasetInspection:
    root = Path(dataset_dir or get_recipe_dataset_dir())
    files = [_file_status(root, name) for name in EXPECTED_FILES]
    warnings = [status.warning for status in files if status.warning]

    csv_preview = None
    normalized_preview = None
    csv_status = _status_for(files, "13k-recipes.csv")
    if csv_status and csv_status.present and csv_status.readable:
        try:
            csv_preview = _inspect_csv(root / "13k-recipes.csv")
            normalized_preview = _normalized_preview(csv_preview)
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            warnings.append(f"Could not inspect 13k-recipes.csv: {exc}")

    sqlite_previews: list[SQLiteSchemaPreview] = []
    for file_name in ("13k-recipes.db", "5k-recipes.db"):
        status = _status_for(files, file_name)
        if status and status.present and status.readable:
            try:
                sqlite_previews.append(SQLiteSchemaPreview(file_name=file_name, tables=inspect_schema(root / file_name)))
            except (OSError, sqlite3.Error) as exc:
                warnings.append(f"Could not inspect {file_name}: {exc}")

    metadata = None
    metadata_status = _status_for(files, "metadata.json")
    if metadata_status and metadata_status.present and metadata_status.readable:
        try:
            metadata = _inspect_metadata(root / "metadata.json")
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"Could not inspect metadata.json: {exc}")

    return DatasetInspection(
        dataset_dir=str(root),
        files=files,
        csv=csv_preview,
        sqlite=sqlite_previews,
        metadata=metadata,
        normalized_preview=normalized_preview,
        warnings=warnings,
    )


def iter_recipe_dataset_records(
    dataset_dir: str | Path | None = None,
    limit: int = 100,
) -> list[ExternalRecipeRecord]:
    if limit <= 0:
        return []

    root = Path(dataset_dir or get_recipe_dataset_dir())
    records: list[ExternalRecipeRecord] = []

    csv_path = root / "13k-recipes.csv"
    if csv_path.is_file():
        records.extend(_read_csv_records(csv_path, limit))

    remaining = limit - len(records)
    if remaining <= 0:
        return records

    for file_name in ("13k-recipes.db", "5k-recipes.db"):
        db_path = root / file_name
        if not db_path.is_file():
            continue
        records.extend(_read_sqlite_records(db_path, remaining))
        remaining = limit - len(records)
        if remaining <= 0:
            break

    return records


def _file_status(root: Path, name: str) -> DatasetFileStatus:
    path = root / name
    if not path.exists():
        return DatasetFileStatus(
            name=name,
            path=str(path),
            present=False,
            readable=False,
            warning=f"{name} is missing.",
        )
    if not path.is_file():
        return DatasetFileStatus(
            name=name,
            path=str(path),
            present=True,
            readable=False,
            warning=f"{name} is not a regular file.",
        )
    try:
        stat = path.stat()
        with path.open("rb"):
            pass
    except OSError as exc:
        return DatasetFileStatus(
            name=name,
            path=str(path),
            present=True,
            readable=False,
            warning=f"{name} is not readable: {exc}",
        )
    return DatasetFileStatus(
        name=name,
        path=str(path),
        present=True,
        readable=True,
        size_bytes=stat.st_size,
        modified_ns=stat.st_mtime_ns,
    )


def _status_for(files: list[DatasetFileStatus], name: str) -> DatasetFileStatus | None:
    return next((status for status in files if status.name == name), None)


def _inspect_csv(path: Path) -> CsvSchemaPreview:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        sample_rows = []
        for row in reader:
            sample_rows.append({key: value or "" for key, value in row.items() if key is not None})
            if len(sample_rows) >= 3:
                break
    return CsvSchemaPreview(
        file_name=path.name,
        columns=columns,
        sample_rows=sample_rows,
        row_count_previewed=len(sample_rows),
    )


def _inspect_metadata(path: Path) -> MetadataPreview:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    values = data if isinstance(data, dict) else {"value": data}
    return MetadataPreview(file_name=path.name, keys=sorted(values.keys()), values=values)


def _normalized_preview(csv_preview: CsvSchemaPreview) -> NormalizedRecipePreview | None:
    if not csv_preview.sample_rows:
        return None
    row = csv_preview.sample_rows[0]
    lower_to_original = {column.lower(): column for column in csv_preview.columns}
    title = _first_value(row, lower_to_original, ("title", "name", "recipe_name"))
    ingredients = _first_value(row, lower_to_original, ("ingredients", "ingredient"))
    instructions = _first_value(row, lower_to_original, ("instructions", "directions", "steps"))
    return NormalizedRecipePreview(
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        source_file=csv_preview.file_name,
    )


def _first_value(row: dict[str, str], columns: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        original = columns.get(candidate)
        if original is not None and row.get(original):
            return row[original]
    return None


def _read_csv_records(path: Path, limit: int) -> list[ExternalRecipeRecord]:
    records: list[ExternalRecipeRecord] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        lower_to_original = {_normalize_column(column): column for column in columns}
        for index, row in enumerate(reader):
            record = _record_from_row(
                row={key: value or "" for key, value in row.items() if key is not None},
                lower_to_original=lower_to_original,
                fallback_id=str(index),
                source_file=path.name,
                source_table=None,
            )
            if record is not None:
                records.append(record)
            if len(records) >= limit:
                break
    return records


def _read_sqlite_records(path: Path, limit: int) -> list[ExternalRecipeRecord]:
    records: list[ExternalRecipeRecord] = []
    try:
        tables = inspect_schema(path)
    except (OSError, sqlite3.Error):
        return records

    recipe_table = _find_recipe_table(tables)
    if recipe_table is None:
        return records

    with open_read_only_sqlite(path) as connection:
        column_names = [column.name for column in recipe_table.columns]
        lower_to_original = {_normalize_column(column): column for column in column_names}
        quoted_columns = ", ".join(_quote_identifier(column) for column in column_names)
        rows = connection.execute(
            f"SELECT {quoted_columns} FROM {_quote_identifier(recipe_table.name)} LIMIT ?",
            (limit,),
        ).fetchall()

    for index, row_values in enumerate(rows):
        row = {column: "" if value is None else str(value) for column, value in zip(column_names, row_values, strict=True)}
        record = _record_from_row(
            row=row,
            lower_to_original=lower_to_original,
            fallback_id=str(index),
            source_file=path.name,
            source_table=recipe_table.name,
        )
        if record is not None:
            records.append(record)

    return records


def _find_recipe_table(tables: list[TableInfo]) -> TableInfo | None:
    for table in tables:
        normalized = {_normalize_column(column.name) for column in table.columns}
        has_title = any(field in normalized for field in TITLE_FIELDS)
        has_ingredients = any(field in normalized for field in INGREDIENT_FIELDS)
        has_instructions = any(field in normalized for field in INSTRUCTION_FIELDS)
        if has_title and (has_ingredients or has_instructions):
            return table
    return None


def _record_from_row(
    row: dict[str, str],
    lower_to_original: dict[str, str],
    fallback_id: str,
    source_file: str,
    source_table: str | None,
) -> ExternalRecipeRecord | None:
    title = _first_value(row, lower_to_original, TITLE_FIELDS)
    if not title:
        return None

    source_id = _first_value(row, lower_to_original, ID_FIELDS) or fallback_id
    ingredients = _split_values(_first_value(row, lower_to_original, INGREDIENT_FIELDS))
    instructions = _split_values(_first_value(row, lower_to_original, INSTRUCTION_FIELDS))
    tags = _split_values(_first_value(row, lower_to_original, TAG_FIELDS))

    return ExternalRecipeRecord(
        source_id=str(source_id),
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        tags=tags,
        source_file=source_file,
        source_table=source_table,
        raw=dict(row),
    )


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    cleaned = value.strip()
    if not cleaned:
        return []
    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            parsed = json.loads(cleaned.replace("'", '"'))
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    parts = [part.strip(" .") for part in cleaned.replace("\r", "\n").split("\n")]
    if len(parts) == 1:
        parts = [part.strip(" .") for part in cleaned.replace(";", "|").split("|")]
    return [part for part in parts if part]


def _normalize_column(column: str) -> str:
    lowered = column.strip().lower()
    return lowered.replace(" ", "_")


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
