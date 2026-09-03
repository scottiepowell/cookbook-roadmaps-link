from pathlib import Path
from types import SimpleNamespace

from app import main


def test_public_compose_mounts_recipe_dataset_read_only_with_bounded_index():
    compose = (Path(__file__).parents[2] / "docker-compose.public.yml").read_text(encoding="utf-8")

    assert "RECIPE_DATASET_DIR: /app/recipe-dataset" in compose
    assert 'RECIPE_DATASET_INDEX_LIMIT: "5000"' in compose
    assert "source: ./recipe-dataset" in compose
    assert "target: /app/recipe-dataset" in compose
    assert "read_only: true" in compose
    assert "create_host_path: false" in compose
    assert 'AI_RECIPE_DATASET_WARM_ON_START: "true"' in compose
    assert "start_period: 120s" in compose


def test_public_compose_does_not_mount_dataset_into_core():
    compose = (Path(__file__).parents[2] / "docker-compose.public.yml").read_text(encoding="utf-8")
    app_section, sidecar_section = compose.split("  ai-api:", maxsplit=1)

    assert "/app/recipe-dataset" not in app_section
    assert "/app/recipe-dataset" in sidecar_section


def test_dataset_warmup_builds_index_only_when_enabled(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_RECIPE_DATASET_WARM_ON_START", "true")
    monkeypatch.setattr(
        main,
        "search_dataset_recipes",
        lambda query, limit: calls.append((query, limit))
        or SimpleNamespace(index=SimpleNamespace(document_count=5000)),
    )

    main.warm_recipe_dataset_on_start()

    assert calls == [("chicken recipe", 1)]


def test_dataset_warmup_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AI_RECIPE_DATASET_WARM_ON_START", raising=False)
    monkeypatch.setattr(
        main,
        "search_dataset_recipes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("warmup should be disabled")),
    )

    main.warm_recipe_dataset_on_start()
