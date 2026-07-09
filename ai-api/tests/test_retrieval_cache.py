import os
from pathlib import Path

from app.dataset_retrieval import search_dataset_recipes
from app.retrieval_cache import (
    describe_dataset_source,
    get_cached_dataset_index,
    get_cached_retrieval_results,
    reset_retrieval_cache,
)


def write_dataset_fixture(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "1,Classic Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham crackers\",\"Beat filling; Bake; Chill\",dessert\n"
        "2,Apple Crumble,\"apples; sugar; butter; oats\",\"Bake until bubbly\",dessert\n",
        encoding="utf-8",
    )


def test_index_cache_hits_after_first_build(tmp_path, monkeypatch):
    reset_retrieval_cache()
    write_dataset_fixture(tmp_path)
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return {"built": calls["count"]}

    value1, meta1, key1 = get_cached_dataset_index(dataset_dir=tmp_path, record_limit=2, build_fn=build_value)
    value2, meta2, key2 = get_cached_dataset_index(dataset_dir=tmp_path, record_limit=2, build_fn=build_value)

    assert value1 == {"built": 1}
    assert value2 == {"built": 1}
    assert calls["count"] == 1
    assert meta1.index_cache_hit is False
    assert meta2.index_cache_hit is True
    assert key1 == key2


def test_index_cache_miss_when_dataset_limit_changes(tmp_path):
    reset_retrieval_cache()
    write_dataset_fixture(tmp_path)
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return {"built": calls["count"]}

    get_cached_dataset_index(dataset_dir=tmp_path, record_limit=2, build_fn=build_value)
    get_cached_dataset_index(dataset_dir=tmp_path, record_limit=3, build_fn=build_value)

    assert calls["count"] == 2


def test_index_cache_miss_when_source_file_metadata_changes(tmp_path):
    reset_retrieval_cache()
    write_dataset_fixture(tmp_path)
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return {"built": calls["count"]}

    get_cached_dataset_index(dataset_dir=tmp_path, record_limit=2, build_fn=build_value)
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "1,Classic Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham crackers\",\"Beat filling; Bake; Chill\",dessert\n"
        "2,Apple Crumble,\"apples; sugar; butter; oats; cream\",\"Bake until bubbly\",dessert\n",
        encoding="utf-8",
    )
    get_cached_dataset_index(dataset_dir=tmp_path, record_limit=2, build_fn=build_value)

    assert calls["count"] == 2


def test_retrieval_cache_hits_for_identical_normalized_query_and_top_k():
    reset_retrieval_cache()
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return [{"id": "1"}]

    results1, meta1, key1 = get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query=" carbonara pasta spaghetti eggs parmesan pancetta black pepper ",
        limit=3,
        build_fn=build_value,
    )
    results2, meta2, key2 = get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query="carbonara pasta spaghetti eggs parmesan pancetta black pepper",
        limit=3,
        build_fn=build_value,
    )

    assert results1 == [{"id": "1"}]
    assert results2 == [{"id": "1"}]
    assert calls["count"] == 1
    assert meta1.retrieval_cache_hit is False
    assert meta2.retrieval_cache_hit is True
    assert key1 == key2


def test_retrieval_cache_miss_when_query_changes():
    reset_retrieval_cache()
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return [{"id": str(calls["count"])}]

    get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        limit=3,
        build_fn=build_value,
    )
    get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query="omelet with eggs cheese maybe onions cooked in butter fold it over",
        limit=3,
        build_fn=build_value,
    )

    assert calls["count"] == 2


def test_retrieval_cache_miss_when_top_k_changes():
    reset_retrieval_cache()
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return [{"id": str(calls["count"])}]

    get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        limit=2,
        build_fn=build_value,
    )
    get_cached_retrieval_results(
        index_cache_key="index-cache-key",
        query="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        limit=3,
        build_fn=build_value,
    )

    assert calls["count"] == 2


def test_cache_max_entry_eviction(monkeypatch):
    reset_retrieval_cache()
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_MAX_ENTRIES", "2")
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return [{"id": str(calls["count"])}]

    for query in ("one", "two", "three"):
        get_cached_retrieval_results(index_cache_key="index-cache-key", query=query, limit=1, build_fn=build_value)
    get_cached_retrieval_results(index_cache_key="index-cache-key", query="one", limit=1, build_fn=build_value)

    assert calls["count"] == 4


def test_cache_ttl_expiration(monkeypatch):
    reset_retrieval_cache()
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_TTL_SECONDS", "1")
    calls = {"count": 0}
    times = {"value": 1000.0}

    def fake_monotonic():
        return times["value"]

    def build_value():
        calls["count"] += 1
        return [{"id": str(calls["count"])}]

    monkeypatch.setattr("app.retrieval_cache.time.monotonic", fake_monotonic)
    get_cached_retrieval_results(index_cache_key="index-cache-key", query="ttl query", limit=1, build_fn=build_value)
    times["value"] = 1002.0
    get_cached_retrieval_results(index_cache_key="index-cache-key", query="ttl query", limit=1, build_fn=build_value)

    assert calls["count"] == 2


def test_cache_disabled_path(monkeypatch):
    reset_retrieval_cache()
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_ENABLED", "false")
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return [{"id": str(calls["count"])}]

    _, meta1, _ = get_cached_retrieval_results(index_cache_key="index-cache-key", query="disabled", limit=1, build_fn=build_value)
    _, meta2, _ = get_cached_retrieval_results(index_cache_key="index-cache-key", query="disabled", limit=1, build_fn=build_value)

    assert calls["count"] == 2
    assert meta1.cache_enabled is False
    assert meta2.cache_enabled is False


def test_public_metadata_uses_safe_fingerprints_only(tmp_path, monkeypatch):
    reset_retrieval_cache()
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = search_dataset_recipes("cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill", limit=2, dataset_limit=2)

    assert response.cache.index_cache_key
    assert response.cache.retrieval_cache_key
    assert str(tmp_path) not in response.cache.index_cache_key
    assert str(tmp_path) not in response.cache.retrieval_cache_key
    assert response.cache.cache_enabled is True
    assert response.cache.cache_entry_count >= 1


def test_cached_retrieval_remains_deterministic_with_fixture_dataset(tmp_path, monkeypatch):
    reset_retrieval_cache()
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response1 = search_dataset_recipes("cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill", limit=2, dataset_limit=2)
    response2 = search_dataset_recipes("cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill", limit=2, dataset_limit=2)

    assert [result.title for result in response1.results] == [result.title for result in response2.results]
    assert response2.cache.retrieval_cache_hit is True
