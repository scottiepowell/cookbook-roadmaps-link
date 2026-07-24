from app.cookbook_import_adapter import FakeCookbookAdapter
from app.cookbook_import_dry_run import dry_run_import_candidate_operation


def draft(**overrides):
    value = {
        "title": "Lemon Beans",
        "description": "Warm beans with lemon.",
        "servings": 4,
        "ingredients": [
            {"name": "beans", "quantity": "2", "unit": "cups", "note": None},
            {"name": "lemon", "quantity": "1", "unit": "medium", "note": None},
        ],
        "instructions": [
            {"step": 1, "text": "Warm the beans gently."},
            {"step": 2, "text": "Add lemon and serve."},
        ],
        "tags": ["dinner"],
        "source": "https://example.com/recipe",
        "notes": "Review before saving.",
    }
    value.update(overrides)
    return value


def test_operation_is_disabled_by_default_with_safe_response():
    response = dry_run_import_candidate_operation(draft())

    assert response.status == "unavailable"
    assert response.result is None
    assert response.errors[0].code == "disabled"
    assert "OPENAI_API_KEY" not in response.model_dump_json()


def test_enabled_operation_returns_mapped_candidate_and_versions():
    response = dry_run_import_candidate_operation(draft(), enabled=True, idempotency_key="dry-run-1")

    assert response.status == "ready"
    assert response.result is not None
    assert response.result.status == "valid"
    assert response.result.candidate.payload.title == "Lemon Beans"
    assert response.contract_version == response.result.contract_version
    assert response.schema_version == response.result.schema_version


def test_operation_returns_validation_errors_and_unsafe_url_safely():
    response = dry_run_import_candidate_operation(
        draft(title="", source="javascript:alert(1)"), enabled=True
    )

    assert response.status == "ready"
    assert {error.field for error in response.errors} == {"title", "source"}
    assert all("alert" not in error.message for error in response.errors)


def test_operation_delegates_duplicate_and_idempotency_results():
    adapter = FakeCookbookAdapter(
        [{"recipe_id": "fixture-1", "title": "Lemon Beans", "ingredients": ["beans", "lemon"]}]
    )

    first = dry_run_import_candidate_operation(draft(), enabled=True, adapter=adapter, idempotency_key="same")
    replay = dry_run_import_candidate_operation(draft(), enabled=True, adapter=adapter, idempotency_key="same")
    conflict = dry_run_import_candidate_operation(
        draft(title="Other Recipe"), enabled=True, adapter=adapter, idempotency_key="same"
    )

    assert first.result.status == "duplicate"
    assert first.result.duplicate_candidates[0].recipe_id == "fixture-1"
    assert replay.result.status == "idempotent_replay"
    assert replay.result.candidate == first.result.candidate
    assert conflict.result.errors[0].code == "key_reuse_conflict"


def test_operation_propagates_schema_mismatch_without_storage_side_effects():
    response = dry_run_import_candidate_operation(
        draft(), enabled=True, contract_version="unknown.v0", schema_version="unknown.v0"
    )

    assert response.result.status == "schema_mismatch"
    assert response.result.candidate is None
    assert response.result.errors[0].code == "schema_mismatch"


def test_operation_envelope_contains_no_raw_provider_or_local_values():
    response = dry_run_import_candidate_operation(
        draft(notes="provider output / prompt / C:\\private\\local.db"), enabled=True
    )
    output = response.model_dump_json()

    assert "provider output" not in output
    assert "prompt" not in output.lower()
    assert "local.db" not in output
    assert "OPENAI_API_KEY" not in output
