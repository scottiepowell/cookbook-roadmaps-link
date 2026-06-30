from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
import sqlite3


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    default: str | None
    primary_key_position: int


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: list[ColumnInfo]


def open_read_only_sqlite(db_path: str | Path) -> sqlite3.Connection:
    resolved = Path(db_path).resolve()
    uri_path = quote(str(resolved).replace("\\", "/"), safe="/:")
    return sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True)


def inspect_schema(db_path: str | Path) -> list[TableInfo]:
    with open_read_only_sqlite(db_path) as connection:
        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        tables: list[TableInfo] = []
        for (table_name,) in table_rows:
            column_rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
            columns = [
                ColumnInfo(
                    name=row[1],
                    type=row[2] or "",
                    nullable=not bool(row[3]),
                    default=row[4],
                    primary_key_position=int(row[5]),
                )
                for row in column_rows
            ]
            tables.append(TableInfo(name=table_name, columns=columns))

        return tables
