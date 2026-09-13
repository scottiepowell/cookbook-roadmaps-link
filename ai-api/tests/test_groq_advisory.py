import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app import groq_advisory
from app.ai_budget_guard import default_provider_budget_tracker
from app.main import app
from app.providers.errors import ProviderCallError
from app.providers.groq_offload import GroqOffloadProvider


def completion(items, finish_reason="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"items": items})), finish_reason=finish_reason)],
        usage=SimpleNamespace(prompt_tokens=40, completion_tokens=20),
    )


class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def provider(outcomes):
    completions = FakeCompletions(outcomes)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return GroqOffloadProvider(api_key="synthetic-test-key", client=client), completions


def test_strict_contract_and_usage():
    active, fake = provider([completion([{"source_id": "s0", "suggestion": "Produce aisle"}])])
    items, usage = active.generate(task="Suggest aisle labels", lines=[{"source_id": "s0", "text": "carrots"}])
    assert items[0]["suggestion"] == "Produce aisle"
    assert usage == {"input_tokens": 40, "output_tokens": 20}
    assert fake.calls[0]["response_format"]["json_schema"]["strict"] is True
    assert fake.calls[0]["model"] == "openai/gpt-oss-20b"


@pytest.mark.parametrize("bad_items", [
    [{"source_id": "s8", "suggestion": "Other"}],
    [{"source_id": "s0", "suggestion": "x", "extra": "x"}],
    [{"source_id": "s0", "suggestion": ""}],
])
def test_unknown_or_invalid_output_rejected(bad_items):
    active, _ = provider([completion(bad_items)])
    with pytest.raises(ProviderCallError):
        active.generate(task="Suggest", lines=[{"source_id": "s0", "text": "carrots"}])


def test_one_transient_retry_and_circuit_breaker():
    error = RuntimeError("temporary")
    error.status_code = 503
    active, fake = provider([error, completion([{"source_id": "s0", "suggestion": "Produce"}])])
    active.generate(task="Suggest", lines=[{"source_id": "s0", "text": "carrots"}])
    assert len(fake.calls) == 2
    failures, _ = provider([completion([{"source_id": "wrong", "suggestion": "x"}])] * 3)
    for _ in range(3):
        with pytest.raises(ProviderCallError):
            failures.generate(task="Suggest", lines=[{"source_id": "s0", "text": "carrots"}])
    with pytest.raises(ProviderCallError, match="temporarily unavailable"):
        failures.generate(task="Suggest", lines=[{"source_id": "s0", "text": "carrots"}])


def test_quantity_preservation_rejects_changed_amount():
    active, _ = provider([completion([{"source_id": "s0", "suggestion": "3 cups rice"}])])
    with pytest.raises(ProviderCallError, match="contract"):
        active.generate(task="Normalize", task_key="ingredient_parse",
                        lines=[{"source_id": "s0", "text": "2 cups rice"}])


def test_route_requires_public_confirmation_and_falls_back(monkeypatch):
    monkeypatch.setenv("AI_OFFLOAD_ENABLED", "true")
    monkeypatch.setenv("AI_OFFLOAD_ALLOWED_TASKS", "shopping_group")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    default_provider_budget_tracker.reset()
    active, _ = provider([completion([{"source_id": "unknown", "suggestion": "Other"}])])
    monkeypatch.setattr(groq_advisory, "_provider", active)
    client = TestClient(app)
    path = "/ai/advisory"
    body = {"task": "shopping_group", "text": "carrots"}
    assert client.post(path, json=body).status_code == 400
    response = client.post(path, json={**body, "public_or_synthetic": True})
    assert response.status_code == 200
    assert response.json()["status"] == "fallback"
    assert response.json()["items"] == [{"source": "carrots", "suggestion": "carrots"}]
    assert client.post(path, json={**body, "text": "someone@example.com", "public_or_synthetic": True}).status_code == 400
