from copy import deepcopy

from app.providers import StructuredLLMRequest
from app.providers.openai_provider import OpenAIProvider
from app.providers.openai_schema import normalize_strict_json_schema
from app.schemas import MealPlanDraft, RecipeImportDraft


def test_recipe_import_root_schema_is_strict_object():
    schema = normalize_strict_json_schema(RecipeImportDraft.model_json_schema())

    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "title",
        "description",
        "servings",
        "ingredients",
        "instructions",
        "tags",
        "source",
        "notes",
    ]


def test_recipe_import_nested_schemas_are_strict_objects():
    schema = normalize_strict_json_schema(RecipeImportDraft.model_json_schema())
    ingredient = schema["$defs"]["RecipeIngredientDraft"]
    instruction = schema["$defs"]["RecipeInstructionDraft"]

    assert ingredient["additionalProperties"] is False
    assert ingredient["required"] == ["name", "quantity", "unit", "note"]
    assert instruction["additionalProperties"] is False
    assert instruction["required"] == ["step", "text"]


def test_recipe_import_nullable_fields_are_preserved():
    schema = normalize_strict_json_schema(RecipeImportDraft.model_json_schema())
    ingredient = schema["$defs"]["RecipeIngredientDraft"]

    assert {"type": "null"} in schema["properties"]["description"]["anyOf"]
    assert {"type": "null"} in ingredient["properties"]["quantity"]["anyOf"]
    assert {"type": "null"} in ingredient["properties"]["unit"]["anyOf"]
    assert {"type": "null"} in ingredient["properties"]["note"]["anyOf"]


def test_meal_plan_defs_are_normalized():
    schema = normalize_strict_json_schema(MealPlanDraft.model_json_schema())
    day = schema["$defs"]["MealPlanDay"]
    slot = schema["$defs"]["MealPlanSlot"]

    assert schema["additionalProperties"] is False
    assert schema["required"] == ["days"]
    assert day["additionalProperties"] is False
    assert day["required"] == ["day", "meals"]
    assert slot["additionalProperties"] is False
    assert slot["required"] == ["slot", "recipe_id", "title", "reason"]


def test_normalizer_does_not_mutate_original_schema():
    original = RecipeImportDraft.model_json_schema()
    before = deepcopy(original)

    normalized = normalize_strict_json_schema(original)

    assert original == before
    assert normalized is not original
    assert "additionalProperties" not in original
    assert original["$defs"]["RecipeIngredientDraft"]["required"] == ["name"]


def test_openai_provider_sends_normalized_schema_without_network_call():
    original_schema = RecipeImportDraft.model_json_schema()
    client = RecordingOpenAIClient()
    provider = OpenAIProvider(api_key="fake-offline-key", model="gpt-test")
    provider._client = client

    response = provider.generate_structured(
        StructuredLLMRequest(
            prompt="Extract lemon beans.",
            system="Return JSON.",
            schema_name="RecipeImportDraft",
            schema=original_schema,
            max_output_tokens=100,
        )
    )

    sent_schema = client.responses.last_kwargs["text"]["format"]["schema"]
    assert response.provider == "openai"
    assert response.data["title"] == "Lemon Beans"
    assert sent_schema["additionalProperties"] is False
    assert sent_schema["required"] == [
        "title",
        "description",
        "servings",
        "ingredients",
        "instructions",
        "tags",
        "source",
        "notes",
    ]
    assert sent_schema["$defs"]["RecipeIngredientDraft"]["additionalProperties"] is False
    assert sent_schema["$defs"]["RecipeIngredientDraft"]["required"] == ["name", "quantity", "unit", "note"]
    assert "additionalProperties" not in original_schema


class RecordingOpenAIClient:
    def __init__(self) -> None:
        self.responses = RecordingResponses()


class RecordingResponses:
    def __init__(self) -> None:
        self.last_kwargs = {}

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeOpenAIResponse()


class FakeOpenAIResponse:
    output_text = (
        '{"title":"Lemon Beans","description":null,'
        '"servings":4,'
        '"ingredients":[{"name":"beans","quantity":null,"unit":null,"note":null}],'
        '"instructions":[{"step":1,"text":"Warm beans."}],'
        '"tags":[],"source":null,"notes":null}'
    )
    usage = None
