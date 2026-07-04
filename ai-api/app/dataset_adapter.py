import csv
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import get_recipe_dataset_dir
from app.schema_inspector import TableInfo, inspect_schema


EXPECTED_FILES = (
    "13k-recipes.csv",
    "13k-recipes.db",
    "5k-recipes.db",
    "metadata.json",
    "README.md",
    "tutorial.md",
)


@dataclass(frozen=True)
class DatasetFileStatus:
    name: str
    path: str
    present: bool
    readable: bool
    size_bytes: int | None = None
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
        size = path.stat().st_size
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
    return DatasetFileStatus(name=name, path=str(path), present=True, readable=True, size_bytes=size)


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
        if original and row.get(original):
            return row[original]
    return None
