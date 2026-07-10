from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.recipe_requirements import extract_recipe_requirements
from app.recipe_session import RecipeSessionStore


def test_session_store_create_and_get():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=60)
    requirements = extract_recipe_requirements("cheesecake with cream cheese sugar eggs vanilla graham cracker crust bake", now=now)

    session = store.create_session(requirements, now=now, interaction_id="rs_test")
    loaded = store.get_session("rs_test", now=now + timedelta(seconds=1))

    assert session.interaction_id == "rs_test"
    assert loaded is not None
    assert loaded.requirements.interaction_id == "rs_test"
    assert loaded.requirements.dish_intent.value == "cheesecake"
    assert store.count(now=now) == 1


def test_session_store_update():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=60)
    original = extract_recipe_requirements("classic baked cheesecake for 4 with cream cheese graham cracker crust", now=now)
    store.create_session(original, now=now, interaction_id="rs_update")

    updated = extract_recipe_requirements("classic no-bake cheesecake for 4 with cream cheese graham cracker crust chill", now=now)
    updated.revision_count = 1
    session = store.update_session("rs_update", updated, now=now + timedelta(seconds=5))

    assert session is not None
    assert session.revision_count == 1
    assert session.requirements.revision_count == 1
    assert session.requirements.cooking_method
    assert "no-bake" in session.requirements.cooking_method.value


def test_session_store_expires_sessions_deterministically():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=10)
    requirements = extract_recipe_requirements("omelet with eggs cheese cooked in a skillet", now=now)
    store.create_session(requirements, now=now, interaction_id="rs_expire")

    assert store.get_session("rs_expire", now=now + timedelta(seconds=9)) is not None
    assert store.expire_sessions(now + timedelta(seconds=11)) == 1
    assert store.get_session("rs_expire", now=now + timedelta(seconds=11)) is None


def test_session_store_evicts_oldest_when_bounded():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=60)

    for index, dish in enumerate(("cheesecake", "carbonara", "omelet"), start=1):
        requirements = extract_recipe_requirements(f"{dish} for 4", now=now)
        store.create_session(requirements, now=now + timedelta(seconds=index), interaction_id=f"rs_{index}")

    assert store.get_session("rs_1", now=now + timedelta(seconds=4)) is None
    assert store.get_session("rs_2", now=now + timedelta(seconds=4)) is not None
    assert store.get_session("rs_3", now=now + timedelta(seconds=4)) is not None
    assert store.count(now=now + timedelta(seconds=4)) == 2


def test_session_store_clear():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=60)
    requirements = extract_recipe_requirements("carbonara with spaghetti egg parmesan pancetta black pepper", now=now)
    store.create_session(requirements, now=now, interaction_id="rs_clear")

    store.clear()

    assert store.count(now=now) == 0
    assert store.get_session("rs_clear", now=now) is None


def test_session_store_safe_serialization_has_no_secret_or_prompt_fields():
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    store = RecipeSessionStore(max_sessions=2, ttl_seconds=60)
    requirements = extract_recipe_requirements("chicken and rice casserole with cooked chicken rice cream of chicken soup cheddar bake", now=now)
    session = store.create_session(requirements, now=now, interaction_id="rs_safe")
    dumped = str(session.model_dump())

    assert "raw_provider" not in dumped
    assert "OPENAI_API_KEY" not in dumped
    assert ".env" not in dumped
    assert "C:\\Users" not in dumped
    assert "Authorization" not in dumped
    assert "long_term" not in dumped
