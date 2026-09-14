import json
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from app import rag_offload, importer
from app.ai_budget_guard import default_provider_budget_tracker
from app.main import app
from app.providers.groq_offload import GroqOffloadProvider
from app.rag_context import PackedImporterContext, PackedImporterContextExample
from app.schemas import RecipeImportRequest
from app.providers.base import StructuredLLMResponse


def pack():
    return PackedImporterContext(query="PRIVATE USER NOTES", retrieved_count=1, packed_count=1,
        packed_ids=["id1"], items=[PackedImporterContextExample(rank=1, id="id1", source_id="1",
        title="Carrot salad", matched_fields=["ingredients"], snippet="2 cups carrots",
        key_ingredients=["2 cups carrots", "1 onion"], instruction_summary="Mix and serve.", relevance_category="strong")])


def response(items):
    return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=40, completion_tokens=20),
        choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps({"items": items})))])


@pytest.fixture
def enabled(monkeypatch):
    for key in ("AI_OFFLOAD_ENABLED", "AI_RAG_GROQ_DEDUP_ENABLED"):
        monkeypatch.setenv(key, "true")
    monkeypatch.setattr(rag_offload, "_approved_dataset", lambda: True)
    monkeypatch.setattr(rag_offload, "check_provider_budget", lambda *a: SimpleNamespace(allowed=True))


def fake(monkeypatch, outcomes):
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=outcomes))))
    provider = GroqOffloadProvider(api_key="generated-test", client=client)
    monkeypatch.setattr(rag_offload, "_provider", provider)
    return client.chat.completions.create


def test_lossless_offload_omits_duplicate_only_and_never_sends_query(enabled, monkeypatch):
    calls = fake(monkeypatch, [response([{"source_id": "s0", "suggestion": "omit"}])])
    before = pack()
    after = rag_offload.optimize_context(before)
    assert after.items[0].snippet == ""
    assert after.items[0].key_ingredients == before.items[0].key_ingredients
    assert after.items[0].instruction_summary == before.items[0].instruction_summary
    assert after.packed_ids == before.packed_ids
    assert "PRIVATE" not in json.dumps(calls.call_args.kwargs)
    assert "2 cups carrots" in after.render_for_prompt()


@pytest.mark.parametrize("bad", ["replace", "omit"])
def test_invalid_or_lossy_omission_falls_back(enabled, monkeypatch, bad):
    before = pack()
    # A second source contains unique negation; overlap is not enough to omit it.
    before = replace(before, items=[*before.items, replace(before.items[0], id="id2", snippet="Do not fry carrots")])
    fake(monkeypatch, [response([{"source_id": "s0", "suggestion": "omit"}, {"source_id": "s1", "suggestion": bad}])])
    assert rag_offload.optimize_context(before) is before


@pytest.mark.parametrize("kind", ["unknown", "timeout", "budget", "missing_key", "unapproved", "concurrency"])
def test_failures_preserve_original(enabled, monkeypatch, kind):
    outcomes = [TimeoutError()] if kind == "timeout" else [response([{"source_id": "bad", "suggestion": "omit"}])]
    calls = fake(monkeypatch, outcomes)
    if kind == "budget": monkeypatch.setattr(rag_offload, "check_provider_budget", lambda *a: SimpleNamespace(allowed=False))
    if kind == "unapproved": monkeypatch.setattr(rag_offload, "_approved_dataset", lambda: False)
    if kind == "missing_key":
        monkeypatch.setattr(rag_offload, "_provider", None)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
    if kind == "concurrency": monkeypatch.setattr(rag_offload, "_slots", SimpleNamespace(acquire=lambda **kw: False))
    before = pack()
    assert rag_offload.optimize_context(before) is before
    if kind in {"budget", "unapproved", "missing_key", "concurrency"}: calls.assert_not_called()


def test_retry_reserves_each_attempt_and_logs_unknown_usage(enabled, monkeypatch):
    transient = RuntimeError()
    transient.status_code = 429
    calls = fake(monkeypatch, [transient, response([{"source_id": "s0", "suggestion": "omit"}])])
    log = Mock()
    budget = Mock(return_value=SimpleNamespace(allowed=True))
    monkeypatch.setattr(rag_offload, "log_event", log)
    monkeypatch.setattr(rag_offload, "check_provider_budget", budget)
    rag_offload.optimize_context(pack())
    assert calls.call_count == budget.call_count == 2
    assert log.call_args.kwargs["input_tokens"] == 40
    assert log.call_args.kwargs["usage_complete"] is False


def test_dataset_pin_invalidates_on_any_source_change(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_offload, "get_recipe_dataset_dir", lambda: str(tmp_path))
    digest = sha256()
    for name in ("13k-recipes.csv", "13k-recipes.db", "5k-recipes.db"):
        (tmp_path / name).write_bytes(b"public fixture")
        digest.update(name.encode()); digest.update(sha256(b"public fixture").digest())
    monkeypatch.setenv("AI_RAG_PUBLIC_DATASET_SHA256", digest.hexdigest())
    assert rag_offload._approved_dataset()
    (tmp_path / "5k-recipes.db").write_bytes(b"private replacement")
    assert not rag_offload._approved_dataset()


def test_disabled_and_no_redundancy_make_no_call(monkeypatch):
    monkeypatch.delenv("AI_RAG_GROQ_DEDUP_ENABLED", raising=False)
    monkeypatch.delenv("AI_RAG_DEDUP_ENABLED", raising=False)
    before = pack()
    assert rag_offload.optimize_context(before) is before
    monkeypatch.setenv("AI_RAG_GROQ_DEDUP_ENABLED", "true")
    no_match = replace(before, items=[])
    assert rag_offload.optimize_context(no_match) is no_match


def test_importer_integration_nano_receives_original_notes_and_preserved_evidence(enabled, monkeypatch):
    fake(monkeypatch, [response([{"source_id": "s0", "suggestion": "omit"}])])
    monkeypatch.setattr(importer, "_retrieve_importer_examples", lambda text: (None, [], [], pack()))
    monkeypatch.setattr(importer, "check_provider_budget", lambda *a: SimpleNamespace(allowed=True))
    final = SimpleNamespace(name="openai", model="gpt-5.4-nano", generate_structured=Mock(return_value=StructuredLLMResponse(
        provider="openai", model="gpt-5.4-nano", data={"title": "Carrot salad", "servings": 4,
        "ingredients": [{"name": "carrots", "quantity": "2", "unit": "cups"}],
        "instructions": [{"step": 1, "text": "Mix carrots and serve."}], "notes": ""})))
    result = importer.import_recipe_text(RecipeImportRequest(text="Carrot salad with carrots and onion. Mix and serve."), provider=final)
    assert result.provider == "openai"
    prompt = final.generate_structured.call_args.args[0].prompt
    assert "Carrot salad with carrots and onion" in prompt
    assert "2 cups carrots" in prompt
    assert "Snippet:" not in prompt


def test_catalog_endpoint_auth_and_metadata_only(monkeypatch):
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN", "generated-catalog-token")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")
    client = TestClient(app)
    assert client.get("/ai/public-recipes").status_code in {401, 403}
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    result = client.get("/ai/public-recipes").json()
    assert result["scope"] == "curated_catalog"
    assert len(result["recipes"]) == 8
    assert all("instructions" not in item for item in result["recipes"])
    assert all(item["url"].startswith("https://") and item["verified"] for item in result["recipes"])
    assert len({item["uid"] for item in result["recipes"]}) == 8
