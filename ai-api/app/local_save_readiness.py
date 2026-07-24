"""Deterministic disposable local Save-to-Cookbook readiness evidence.

This module is only used by the explicitly approved local readiness script. It
contains no HTTP client, provider call, production target, or product route.
The write path accepts only its fixed synthetic fixture and is intended for the
ignored cookbook-local SQLite database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIXTURE_TITLE = "Local Readiness Beans"
FIXTURE_DESCRIPTION = "Synthetic local readiness recipe."
FIXTURE_SERVINGS = 4
FIXTURE_SOURCE = "local-readiness-fixture"
FIXTURE_SOURCE_URL = "https://example.invalid/cookbook-readiness"
FIXTURE_NOTES = "Imported from AI draft; reviewed in disposable test."
FIXTURE_INGREDIENTS = (
    {"name": "beans", "quantity": "2", "unit": "cups", "note": None},
    {"name": "lemon", "quantity": "1", "unit": "medium", "note": None},
)
FIXTURE_INSTRUCTIONS = (
    {"step": 1, "text": "Warm the beans gently."},
    {"step": 2, "text": "Add lemon and serve."},
)


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def serialize_ingredient(item: dict[str, Any]) -> str:
    parts = [_clean(item.get("quantity")), _clean(item.get("unit")), _clean(item.get("name"))]
    result = " ".join(part for part in parts if part)
    note = _clean(item.get("note"))
    return f"{result} ({note})" if note else result


def serialize_ingredients(items: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> str:
    return "\n".join(serialize_ingredient(item) for item in items)


def serialize_directions(items: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> str:
    expected = list(range(1, len(items) + 1))
    actual = [int(item["step"]) for item in items]
    if actual != expected or any(not _clean(item.get("text")) for item in items):
        raise ValueError("fixture instruction steps are not contiguous")
    return "\n".join(f"{item['step']}. {_clean(item['text'])}" for item in items)


def fixture_payload() -> dict[str, Any]:
    ingredients = serialize_ingredients(FIXTURE_INGREDIENTS)
    directions = serialize_directions(FIXTURE_INSTRUCTIONS)
    return {
        "name": FIXTURE_TITLE,
        "description": FIXTURE_DESCRIPTION,
        "servings": str(FIXTURE_SERVINGS),
        "ingredients": ingredients,
        "directions": directions,
        "source": FIXTURE_SOURCE,
        "source_url": FIXTURE_SOURCE_URL,
        "notes": FIXTURE_NOTES,
        "is_public": False,
    }


def _fingerprint(user_id: str, payload: dict[str, Any]) -> str:
    material = json.dumps(
        {"user_id": user_id, "name": payload["name"].casefold(), "ingredients": payload["ingredients"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:24]


def _connect_write(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _connect_read(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def _read_recipe(db_path: Path, user_id: str, recipe_id: str) -> dict[str, Any] | None:
    with _connect_read(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT uid, userId, name, description, servings, ingredients, directions, source, source_url, notes "
            "FROM Recipe WHERE uid = ? AND userId = ?",
            (recipe_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def write_fixture_once(db_path: Path) -> dict[str, Any]:
    """Write exactly one synthetic user/recipe and exercise no-second-write paths."""

    user_id = str(uuid.uuid4())
    recipe_id = str(uuid.uuid4())
    failed_recipe_id = str(uuid.uuid4())
    payload = fixture_payload()
    idempotency_key = f"local-readiness-{_fingerprint(user_id, payload)}"
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    with _connect_write(db_path) as connection:
        connection.execute("BEGIN")
        connection.execute(
            "INSERT INTO auth_user (id, username, publicRecipes) VALUES (?, ?, ?)",
            (user_id, f"local-readiness-{user_id[:8]}", False),
        )
        connection.execute(
            "INSERT INTO Recipe (uid, userId, name, description, servings, ingredients, directions, source, source_url, notes, is_public, created) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                recipe_id,
                user_id,
                payload["name"],
                payload["description"],
                payload["servings"],
                payload["ingredients"],
                payload["directions"],
                payload["source"],
                payload["source_url"],
                payload["notes"],
                payload["is_public"],
                created,
            ),
        )
        connection.commit()

    row = _read_recipe(db_path, user_id, recipe_id)
    if row is None:
        raise RuntimeError("read-after-write did not find the synthetic recipe")
    expected_fields = {key: payload[key] for key in payload if key != "is_public"}
    if any(row[key] != value for key, value in expected_fields.items()):
        raise RuntimeError("serialized synthetic recipe did not round-trip")

    duplicate_rows = _read_recipe(db_path, user_id, recipe_id)
    duplicate_status = "duplicate-prevented" if duplicate_rows else "duplicate-check-failed"
    replay_status = "idempotent-replay" if idempotency_key == f"local-readiness-{_fingerprint(user_id, payload)}" else "idempotency-failed"
    conflict_status = "idempotency-conflict-prevented" if idempotency_key != f"local-readiness-{_fingerprint(user_id, {**payload, 'name': 'Changed fixture'})}" else "idempotency-conflict-failed"

    failure_status = "failure-rollback-passed"
    with _connect_write(db_path) as connection:
        try:
            connection.execute("BEGIN")
            connection.execute(
                "INSERT INTO Recipe (uid, userId, name, servings, ingredients, directions, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (failed_recipe_id, "missing-synthetic-user", "failure fixture", "4", "failure", "1. failure", created),
            )
            connection.commit()
            failure_status = "failure-injection-did-not-fail"
        except sqlite3.IntegrityError:
            connection.rollback()
            if _read_recipe(db_path, "missing-synthetic-user", failed_recipe_id) is not None:
                failure_status = "failure-rollback-failed"

    return {
        "status": "write-and-verify-passed",
        "synthetic_user_id": user_id,
        "synthetic_recipe_id": recipe_id,
        "serialization_status": "round-trip-passed",
        "ownership_status": "synthetic-owner-passed",
        "duplicate_status": duplicate_status,
        "idempotency_status": f"{replay_status};{conflict_status}",
        "failure_status": failure_status,
        "media_status": "excluded",
        "category_status": "excluded",
        "embedding_status": "excluded",
    }


def verify_fixture_read(db_path: Path, user_id: str, recipe_id: str) -> dict[str, str]:
    row = _read_recipe(db_path, user_id, recipe_id)
    if row is None:
        raise RuntimeError("synthetic recipe is not readable")
    return {"status": "read-after-write-passed", "recipe_id": recipe_id}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--mode", choices=("write", "verify"), required=True)
    parser.add_argument("--user-id")
    parser.add_argument("--recipe-id")
    args = parser.parse_args()
    db_path = Path(args.db)
    result = write_fixture_once(db_path) if args.mode == "write" else verify_fixture_read(db_path, args.user_id or "", args.recipe_id or "")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
