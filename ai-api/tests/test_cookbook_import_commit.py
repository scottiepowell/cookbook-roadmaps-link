from app.cookbook_import_commit import (
    InMemoryLocalCookbookStore,
    LocalCommitGuard,
    LocalCookbookCommitService,
    validate_local_commit_guard,
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
        "tags": ["dinner"],
        "source": "https://example.invalid/fixture",
        "notes": "Reviewed local fixture.",
    }
    value.update(overrides)
    return value


def approved_guard(**overrides):
    value = {
        "enabled": True,
        "approved": True,
        "runtime_verified": True,
        "target_url": "http://127.0.0.1:3000/",
    }
    value.update(overrides)
    return LocalCommitGuard(**value)


def test_commit_is_disabled_by_default_and_does_not_write():
    store = InMemoryLocalCookbookStore()
    result = LocalCookbookCommitService(store=store).commit(draft())

    assert result.status == "unavailable"
    assert result.errors[0].code == "disabled"
    assert store.recipes == {}


def test_guard_refuses_exposed_and_non_loopback_targets():
    exposed = validate_local_commit_guard(approved_guard(target_url="https://cookbook.roadmaps.link/"))
    non_loopback = validate_local_commit_guard(approved_guard(target_url="http://192.168.1.5:3000/"))

    assert {error.code for error in exposed} >= {"non_local_target", "non_loopback"}
    assert any(error.code == "non_loopback" for error in non_loopback)


def test_valid_commit_uses_schema_informed_serialization_and_safe_result():
    store = InMemoryLocalCookbookStore()
    result = LocalCookbookCommitService(store=store).commit(draft(), guard=approved_guard(), idempotency_key="local-1")

    assert result.status == "committed"
    assert result.local_recipe_id
    assert len(store.recipes) == 1
    stored = next(iter(store.recipes.values()))
    assert stored["owner_id"] == "synthetic-local-owner"
    assert stored["payload"]["servings"] == "4"
    assert stored["payload"]["ingredients"] == "2 cups beans\n1 medium lemon"
    assert stored["payload"]["directions"] == "1. Warm the beans gently.\n2. Add lemon and serve."
    assert stored["payload"]["categories"] is None
    assert stored["payload"]["media"] is None
    assert result.model_dump_json().find("beans") == -1
    assert result.model_dump_json().find("OPENAI_API_KEY") == -1


def test_duplicate_replay_and_key_conflict_do_not_create_unbounded_writes():
    store = InMemoryLocalCookbookStore()
    service = LocalCookbookCommitService(store=store)
    first = service.commit(draft(), guard=approved_guard(), idempotency_key="local-1")
    replay = service.commit(draft(), guard=approved_guard(), idempotency_key="local-1")
    duplicate = service.commit(draft(), guard=approved_guard(), idempotency_key="local-2")
    conflict = service.commit(draft(title="Other Recipe"), guard=approved_guard(), idempotency_key="local-1")

    assert first.status == "committed"
    assert replay.status == "idempotent_replay"
    assert replay.local_recipe_id == first.local_recipe_id
    assert duplicate.status == "duplicate"
    assert conflict.status == "conflict"
    assert len(store.recipes) == 1


def test_invalid_candidate_and_schema_mismatch_are_safe_errors():
    service = LocalCookbookCommitService()
    invalid = service.commit(draft(title="", instructions=[]), guard=approved_guard())
    mismatch = service.commit(draft(), guard=approved_guard(), schema_version="unknown.v0")

    assert invalid.status == "invalid"
    assert {error.field for error in invalid.errors} >= {"title", "instructions"}
    assert mismatch.status == "invalid"
    assert mismatch.errors[0].code == "schema_mismatch"


def test_failure_injection_rolls_back_without_leaking_storage_details():
    store = InMemoryLocalCookbookStore(failure_after_insert=True)
    result = LocalCookbookCommitService(store=store).commit(draft(), guard=approved_guard())

    assert result.status == "unavailable"
    assert result.errors[0].code == "local_transaction_failed"
    assert store.recipes == {}
    output = result.model_dump_json()
    assert "sqlite" not in output.lower()
    assert "prompt" not in output.lower()
    assert "C:\\" not in output
