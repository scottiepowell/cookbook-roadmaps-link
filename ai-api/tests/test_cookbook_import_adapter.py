from app.cookbook_import_adapter import (
    CONTRACT_VERSION,
    RECIPE_SCHEMA_VERSION,
    FakeCookbookAdapter,
    map_import_draft_to_candidate,
)


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
        "tags": [" Dinner ", "dinner"],
        "source": "https://example.com/recipe",
        "notes": "Review estimated quantities.",
    }
    value.update(overrides)
    return value


def test_valid_draft_maps_to_safe_candidate_payload():
    result = map_import_draft_to_candidate(draft(), idempotency_key="fixture-1")

    assert result.status == "valid"
    assert result.candidate is not None
    assert result.candidate.payload.title == "Lemon Beans"
    assert [tag for tag in result.candidate.payload.tags] == ["dinner"]
    assert result.candidate.payload.ingredients[0].name == "beans"
    assert result.candidate.payload.instructions[1].step == 2
    assert result.candidate.idempotency_key == "fixture-1"
    assert result.schema_version == RECIPE_SCHEMA_VERSION


def test_missing_title_and_instructions_return_field_errors():
    missing_title = map_import_draft_to_candidate(draft(title=""))
    missing_instructions = map_import_draft_to_candidate(draft(instructions=[]))

    assert missing_title.status == "invalid"
    assert any(error.field == "title" for error in missing_title.errors)
    assert missing_instructions.status == "invalid"
    assert any(error.field == "instructions" for error in missing_instructions.errors)


def test_blank_ingredient_and_empty_step_return_field_errors():
    result = map_import_draft_to_candidate(
        draft(
            ingredients=[{"name": "", "quantity": None, "unit": None, "note": None}],
            instructions=[{"step": 1, "text": ""}],
        )
    )

    assert result.status == "invalid"
    assert any(error.field == "ingredients.0.name" for error in result.errors)
    assert any(error.field == "instructions.0.text" for error in result.errors)


def test_non_contiguous_steps_are_rejected():
    result = map_import_draft_to_candidate(
        draft(instructions=[{"step": 1, "text": "Warm the beans."}, {"step": 3, "text": "Serve."}])
    )

    assert result.status == "invalid"
    assert any(error.code == "non_contiguous" for error in result.errors)


def test_long_fields_are_bounded_without_leaking_values():
    secret_like = "provider-body-not-for-storage"
    result = map_import_draft_to_candidate(draft(title="T" * 201, notes="N" * 4001))
    output = result.model_dump_json()

    assert result.status == "invalid"
    assert {error.field for error in result.errors} == {"title", "notes"}
    assert secret_like not in output
    assert "prompt" not in output.lower()
    assert "provider" not in output.lower()


def test_unknown_fields_are_rejected_explicitly():
    result = map_import_draft_to_candidate(draft(unknown_provider_output="do not store"))

    assert result.status == "invalid"
    assert result.errors[0].code == "unknown_field"
    assert result.errors[0].field == "draft.unknown_provider_output"
    assert "do not store" not in result.model_dump_json()


def test_unsafe_source_url_is_rejected():
    result = map_import_draft_to_candidate(draft(source="javascript:alert(1)"))

    assert result.status == "invalid"
    assert any(error.code == "unsafe_url" for error in result.errors)


def test_duplicate_and_idempotent_replay_are_safe():
    adapter = FakeCookbookAdapter(
        [{"recipe_id": "fixture-42", "title": "Lemon Beans", "ingredients": ["beans", "lemon"]}]
    )

    first = adapter.dry_run_import_candidate(draft(), idempotency_key="same-key")
    replay = adapter.dry_run_import_candidate(draft(), idempotency_key="same-key")

    assert first.status == "duplicate"
    assert first.duplicate_candidates[0].recipe_id == "fixture-42"
    assert replay.status == "idempotent_replay"
    assert replay.candidate == first.candidate
    assert replay.idempotency.replayed is True


def test_idempotency_key_reuse_for_different_candidate_is_rejected():
    adapter = FakeCookbookAdapter()
    adapter.dry_run_import_candidate(draft(), idempotency_key="same-key")
    result = adapter.dry_run_import_candidate(draft(title="Different Recipe"), idempotency_key="same-key")

    assert result.status == "invalid"
    assert result.errors[0].code == "key_reuse_conflict"


def test_schema_and_contract_mismatch_are_safe():
    result = map_import_draft_to_candidate(
        draft(), contract_version="cookbook-import.v0", schema_version="unknown.v0"
    )

    assert result.status == "schema_mismatch"
    assert result.candidate is None
    assert result.errors[0].code == "schema_mismatch"
    assert result.contract_version == "cookbook-import.v0"
    assert result.schema_version == "unknown.v0"


def test_contract_version_constants_are_explicit():
    result = map_import_draft_to_candidate(draft())

    assert result.contract_version == CONTRACT_VERSION
    assert result.idempotency.key.startswith("draft-")
