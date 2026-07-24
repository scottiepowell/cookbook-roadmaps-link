import sqlite3
import subprocess
from pathlib import Path

from app.local_save_readiness import (
    FIXTURE_TITLE,
    fixture_payload,
    serialize_directions,
    serialize_ingredients,
    verify_fixture_read,
    write_fixture_once,
)


SCRIPT = Path(__file__).parents[2] / "scripts" / "test-save-to-cookbook-local-readiness.ps1"


def create_fixture_db(path: Path):
    with sqlite3.connect(path) as db:
        db.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE auth_user (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                publicRecipes BOOLEAN NOT NULL DEFAULT 0
            );
            CREATE TABLE Recipe (
                uid TEXT PRIMARY KEY,
                userId TEXT NOT NULL,
                name TEXT,
                description TEXT,
                servings TEXT,
                ingredients TEXT,
                directions TEXT,
                source TEXT,
                source_url TEXT,
                notes TEXT,
                is_public BOOLEAN DEFAULT 0,
                created DATETIME NOT NULL,
                FOREIGN KEY (userId) REFERENCES auth_user(id)
            );
            """
        )


def test_schema_informed_serialization_is_deterministic():
    payload = fixture_payload()

    assert serialize_ingredients(({"quantity": "2", "unit": "cups", "name": "beans", "note": None},)) == "2 cups beans"
    assert serialize_directions(({"step": 1, "text": "Warm the beans."},)) == "1. Warm the beans."
    assert payload["servings"] == "4"
    assert payload["name"] == FIXTURE_TITLE
    assert payload["source_url"].startswith("https://example.invalid/")
    assert payload["is_public"] is False


def test_local_fixture_write_ownership_round_trip_duplicate_and_failure(tmp_path):
    db_path = tmp_path / "dev.sqlite"
    create_fixture_db(db_path)

    result = write_fixture_once(db_path)
    read_result = verify_fixture_read(db_path, result["synthetic_user_id"], result["synthetic_recipe_id"])

    assert result["status"] == "write-and-verify-passed"
    assert result["serialization_status"] == "round-trip-passed"
    assert result["ownership_status"] == "synthetic-owner-passed"
    assert result["duplicate_status"] == "duplicate-prevented"
    assert result["idempotency_status"] == "idempotent-replay;idempotency-conflict-prevented"
    assert result["failure_status"] == "failure-rollback-passed"
    assert read_result["status"] == "read-after-write-passed"
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM Recipe").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM auth_user").fetchone()[0] == 1


def test_local_readiness_script_requires_approval_without_starting_docker():
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    output = (result.stdout + result.stderr).lower()
    assert "approve" in output
    assert "127.0.0.1" not in output
    assert "cookbook.roadmaps.link" not in output


def test_local_readiness_script_refuses_exposed_target_before_write():
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-ApproveLocalWrite",
            "-CookbookTargetUrl",
            "https://cookbook.roadmaps.link/",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    output = (result.stdout + result.stderr).lower()
    assert "readiness evidence did not complete" in output
    assert "cookbook.roadmaps.link" not in output
