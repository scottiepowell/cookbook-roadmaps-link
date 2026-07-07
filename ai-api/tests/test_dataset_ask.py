from fastapi.testclient import TestClient

from app.dataset_rag import ask_dataset_recipes
from app.main import app
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.schemas import DatasetAskRequest


def clear_provider_env(monkeypatch):
    for name in (
        "AI_PROVIDER",
        "AI_MODEL",
        "AI_MAX_OUTPUT_TOKENS",
        "AI_TIMEOUT_SECONDS",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_FALLBACK_MODEL",
        "OPENAI_ENABLE_LIVE_TESTS",
    ):
        monkeypatch.delenv(name, raising=False)


def write_dataset_fixture(path):
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "abc,Lemon Beans,\"beans; lemon\",\"Warm beans\",dinner\n"
        "def,Toast,bread,\"Toast bread\",breakfast\n",
        encoding="utf-8",
    )


def test_dataset_ask_retrieves_context_and_calls_provider(tmp_path, monkeypatch):
    provider = RecordingProvider()
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = ask_dataset_recipes(
        DatasetAskRequest(question="What uses lemon?", limit=2, dataset_limit=2),
        provider=provider,
    )

    assert response.provider == "recording"
    assert response.model == "recording-model"
    assert response.answer == "Grounded dataset answer."
    assert response.retrieval.retrieved_count == 1
    assert response.retrieval.matched_result_ids == ["13k-recipes.csv:abc"]
    assert response.citations[0].source_id == "abc"
    assert response.citations[0].title == "Lemon Beans"
    assert response.citations[0].provenance.license == "CC BY-SA 3.0"
    assert "Lemon Beans" in provider.last_prompt
    assert "Toast" not in provider.last_prompt
    assert str(tmp_path) not in provider.last_prompt


def test_dataset_ask_endpoint_uses_mock_provider_and_cites_dataset(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).post(
        "/dataset/ask",
        json={"question": "What recipe uses lemon?", "limit": 2, "dataset_limit": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["model"] == "mock-basic"
    assert data["retrieval"]["retrieved_count"] == 1
    assert data["citations"][0]["source_id"] == "abc"
    assert data["citations"][0]["provenance"]["dataset"] == "Food Ingredients and Recipes Dataset with Images"
    assert data["citations"][0]["provenance"]["license_url"] == "https://creativecommons.org/licenses/by-sa/3.0/"
    assert "OPENAI_API_KEY" not in response.text
    assert "sk-" not in response.text
    assert "Authorization" not in response.text
    assert str(tmp_path) not in response.text


def test_dataset_ask_no_match_does_not_call_provider(tmp_path, monkeypatch):
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = ask_dataset_recipes(
        DatasetAskRequest(question="Which indexed recipe uses saffron?", limit=2, dataset_limit=2),
        provider=FailingProvider(),
    )

    assert response.provider == "none"
    assert response.model == "none"
    assert response.citations == []
    assert response.retrieval.retrieved_count == 0
    assert "No matching indexed dataset recipes were found; no provider call was made." in response.warnings
    assert "saffron" not in response.answer.lower()


def test_dataset_ask_missing_dataset_returns_warning_without_provider(tmp_path, monkeypatch):
    missing_dir = tmp_path / "missing"
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(missing_dir))

    response = ask_dataset_recipes(
        DatasetAskRequest(question="What uses lemon?", limit=2, dataset_limit=2),
        provider=FailingProvider(),
    )

    assert response.provider == "none"
    assert response.citations == []
    assert response.retrieval.index.document_count == 0
    assert "Configured recipe dataset directory does not exist." in response.warnings
    assert str(missing_dir) not in response.model


def test_dataset_ask_rejects_empty_question(monkeypatch):
    clear_provider_env(monkeypatch)

    response = TestClient(app).post("/dataset/ask", json={"question": "   "})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["citations"] == []
    assert data["input_quality"]["status"] == "rejected"


def test_dataset_ask_does_not_create_index_artifacts(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    write_dataset_fixture(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = TestClient(app).post("/dataset/ask", json={"question": "What uses lemon?", "dataset_limit": 2})

    assert response.status_code == 200
    assert not list(tmp_path.glob("*.index"))
    assert not list(tmp_path.glob("*.idx"))


class RecordingProvider(LLMProvider):
    name = "recording"
    model = "recording-model"

    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        self.last_prompt = request.prompt
        return LLMResponse(
            text="Grounded dataset answer.",
            provider=self.name,
            model=self.model,
            usage={"input_tokens": 12, "output_tokens": 4},
        )

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        return StructuredLLMResponse(data={}, provider=self.name, model=self.model)


class FailingProvider(LLMProvider):
    name = "failing"
    model = "failing-model"

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("Provider should not be called.")

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        raise AssertionError("Provider should not be called.")
