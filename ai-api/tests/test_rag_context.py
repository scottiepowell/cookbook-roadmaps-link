import json
from pathlib import Path

from app.importer import _build_prompt, import_recipe_text
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.rag_context import (
    DEFAULT_IMPORTER_CONTEXT_MAX_CHARS,
    DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES,
    pack_importer_rag_context,
)
from app.schemas import DatasetSearchProvenance, DatasetSearchResult, RecipeImportRequest


def write_context_fixture_dataset(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "strong-1,Classic Baked Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham crackers\",\"Preheat oven; Press crust into pan; Beat filling; Bake until set; Cool and chill\",dessert\n"
        "strong-2,No-Bake Cheesecake Bars,\"cream cheese; sugar; whipped cream; graham crackers; vanilla\",\"Press crust into pan; Mix filling; Chill until set; Slice and serve\",dessert\n"
        "weak-1,Apple Crumble with Vanilla Ice Cream,\"apples; sugar; butter; oats; cream\",\"Prep apples; Mix topping; Bake until bubbly; Serve with ice cream\",dessert\n"
        "weak-2,Pear Tart with Creme Fraiche,\"pears; sugar; butter; flour; creme fraiche\",\"Prepare crust; Arrange pears; Bake; Cool before serving\",dessert\n",
        encoding="utf-8",
    )


def make_result(recipe_id: str, title: str, score: int, snippet: str, matched_fields: list[str]) -> DatasetSearchResult:
    return DatasetSearchResult(
        id=f"13k-recipes.csv:{recipe_id}",
        source_id=recipe_id,
        title=title,
        score=score,
        matched_fields=matched_fields,
        snippet=snippet,
        source_file="13k-recipes.csv",
        source_table=None,
        provenance=DatasetSearchProvenance(
            source_file="13k-recipes.csv",
            source_table=None,
            source_id=recipe_id,
        ),
    )


def test_context_packer_prefers_strong_examples_and_drops_weak(tmp_path):
    write_context_fixture_dataset(tmp_path)
    results = [
        make_result("strong-1", "Classic Baked Cheesecake", 120, "Strong cheesecake snippet", ["title", "ingredients"]),
        make_result("strong-2", "No-Bake Cheesecake Bars", 90, "Strong no-bake snippet", ["title", "instructions"]),
        make_result("weak-1", "Apple Crumble with Vanilla Ice Cream", 22, "Weak crumble snippet", ["title"]),
    ]

    pack = pack_importer_rag_context(
        "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        results,
        dataset_dir=tmp_path,
        dataset_limit=5000,
    )

    assert pack.max_examples == DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES
    assert pack.max_context_chars == DEFAULT_IMPORTER_CONTEXT_MAX_CHARS
    assert pack.packed_ids == ["13k-recipes.csv:strong-1", "13k-recipes.csv:strong-2"]
    assert pack.dropped_ids == ["13k-recipes.csv:weak-1"]
    assert pack.weak_examples_included is False
    assert pack.context_budget_warning is None
    assert "Apple Crumble" not in pack.render_for_prompt()


def test_context_packer_includes_weak_examples_only_when_no_strong_exist(tmp_path):
    write_context_fixture_dataset(tmp_path)
    results = [
        make_result("weak-1", "Apple Crumble with Vanilla Ice Cream", 18, "Weak crumble snippet", ["title"]),
        make_result("weak-2", "Pear Tart with Creme Fraiche", 11, "Weak pear snippet", ["title"]),
    ]

    pack = pack_importer_rag_context(
        "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        results,
        dataset_dir=tmp_path,
        dataset_limit=5000,
    )

    assert pack.packed_ids == ["13k-recipes.csv:weak-1", "13k-recipes.csv:weak-2"]
    assert pack.weak_examples_included is True
    assert pack.context_budget_warning is None
    prompt_block = pack.render_for_prompt()
    assert "weak/structure-only" in prompt_block
    assert "Apple Crumble" in prompt_block


def test_context_packer_truncates_long_fields_and_stays_under_budget(tmp_path):
    path = tmp_path
    path.mkdir(parents=True, exist_ok=True)
    long_ingredients = "; ".join(f"ingredient {index} with a very long descriptive label" for index in range(1, 20))
    long_instructions = "; ".join(f"Step {index}: do a very long thing that keeps going and going" for index in range(1, 12))
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        f"long-1,Long Context Dish,\"{long_ingredients}\",\"{long_instructions}\",test\n",
        encoding="utf-8",
    )
    results = [
        make_result("long-1", "Long Context Dish", 120, "A long snippet that should be truncated safely.", ["title", "ingredients", "instructions"]),
    ]

    pack = pack_importer_rag_context(
        "long context dish",
        results,
        dataset_dir=path,
        dataset_limit=5000,
        max_examples=2,
        max_context_chars=420,
        max_snippet_chars=80,
        max_ingredient_chars=80,
        max_instruction_chars=100,
    )

    assert pack.packed_context_chars <= 420
    assert len(pack.items) == 1
    assert all(len(item.snippet) <= 80 for item in pack.items)
    assert all(len(", ".join(item.key_ingredients)) <= 80 for item in pack.items)
    assert all(len(item.instruction_summary) <= 100 for item in pack.items)
    prompt_block = pack.render_for_prompt()
    assert len(prompt_block) <= 500
    assert "very long descriptive label" not in prompt_block or "..." in prompt_block


def test_importer_prompt_uses_packed_context_and_response_metadata(tmp_path, monkeypatch):
    write_context_fixture_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    provider = CapturingProvider(
        {
            "title": "Classic Cheesecake (Graham Cracker Crust)",
            "description": "A cheesecake draft.",
            "ingredients": [
                {"name": "cream cheese", "quantity": None, "unit": None, "note": None},
                {"name": "graham crackers", "quantity": None, "unit": None, "note": None},
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [
                {"step": 1, "text": "Preheat the oven."},
                {"step": 2, "text": "Bake the cheesecake."},
                {"step": 3, "text": "Chill until firm."},
            ],
            "tags": ["dessert"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(RecipeImportRequest(text="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill"), provider=provider)

    assert response.retrieval is not None
    assert response.retrieval.packed_count <= response.retrieval.retrieved_count
    assert response.retrieval.packed_context_chars <= response.retrieval.max_context_chars
    assert response.retrieval.packed_ids == [citation.id for citation in response.citations[: response.retrieval.packed_count]]
    assert response.retrieval.weak_examples_included is False
    assert response.retrieval.context_budget_warning is None
    assert "Retrieved dataset examples for structure only" in provider.last_request.prompt
    assert "Example 1 [strong]" in provider.last_request.prompt
    assert "Apple Crumble" not in provider.last_request.prompt
    assert str(tmp_path) not in provider.last_request.prompt
    assert "C:\\" not in json.dumps(response.model_dump(), sort_keys=True)


def test_build_prompt_can_render_packed_context_only(tmp_path):
    write_context_fixture_dataset(tmp_path)
    prompt = _build_prompt(
        RecipeImportRequest(text="omelet with eggs cheese maybe onions cooked in butter fold it over"),
        [],
        context_pack=pack_importer_rag_context(
            "omelet with eggs cheese maybe onions cooked in butter fold it over",
            [
                make_result("omelet-1", "Cheese Omelet", 100, "Beat eggs; cook in butter; fold and serve", ["title", "instructions"]),
            ],
            dataset_dir=tmp_path,
            dataset_limit=5000,
        ),
    )

    assert "Retrieved dataset examples for structure only" in prompt
    assert "Example 1" in prompt


class CapturingProvider(LLMProvider):
    name = "capture"
    model = "capture-model"

    def __init__(self, data: dict):
        self.data = data
        self.last_request: StructuredLLMRequest | None = None

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="", provider=self.name, model=self.model)

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        self.last_request = request
        return StructuredLLMResponse(data=self.data, provider=self.name, model=self.model)
