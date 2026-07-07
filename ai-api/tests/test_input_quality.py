import importlib.util
import shutil
import sys
from pathlib import Path

from app.dataset_retrieval import search_dataset_recipes
from app.importer import import_recipe_text
from app.input_quality import NEEDS_CLARIFICATION, READY, REJECTED, WEAK_BUT_USABLE
from app.input_quality import (
    classify_dataset_search_input,
    classify_meal_plan_preferences,
    classify_question_input,
    classify_recipe_import_input,
)
from app.meal_plan_endpoint import create_meal_plan
from app.providers.base import LLMProvider, LLMRequest, StructuredLLMRequest
from app.schemas import MealPlanRequest, RecipeImportRequest


def load_live_eval_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "live-openai-demo-evals.py"
    spec = importlib.util.spec_from_file_location("live_openai_demo_evals", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_input_quality_classifier_statuses():
    assert classify_recipe_import_input("").status == REJECTED
    assert classify_recipe_import_input("     ").status == REJECTED
    assert classify_recipe_import_input("123456789").status == REJECTED
    assert classify_recipe_import_input("!!!!!").status == REJECTED
    assert classify_recipe_import_input("????????").status == REJECTED
    assert classify_recipe_import_input("asdfasdfasdf").status == REJECTED
    assert classify_recipe_import_input("recipe").status == REJECTED
    assert classify_recipe_import_input("make food").status == NEEDS_CLARIFICATION
    assert classify_recipe_import_input("Lemon beans toast").status == WEAK_BUT_USABLE
    assert classify_recipe_import_input("Lemon beans with olive oil, garlic, parsley, and toast. Warm and serve.").status == READY


def test_question_dataset_and_meal_plan_classifiers():
    assert classify_question_input("food").status == REJECTED
    assert classify_question_input("make food").status == NEEDS_CLARIFICATION
    assert classify_question_input("lemon").status == WEAK_BUT_USABLE
    assert classify_question_input("What saved recipe uses lemon?").status == READY

    assert classify_dataset_search_input("%%%%").status == REJECTED
    assert classify_dataset_search_input("make food").status == NEEDS_CLARIFICATION
    assert classify_dataset_search_input("lemon").status == READY

    assert classify_meal_plan_preferences("plan dinner").status == NEEDS_CLARIFICATION
    assert classify_meal_plan_preferences("lemon").status == WEAK_BUT_USABLE
    assert classify_meal_plan_preferences("lemon dinner").status == READY


def test_importer_rejects_and_clarifies_without_provider_call():
    rejected = import_recipe_text(RecipeImportRequest(text="!!!!!"), provider=FailingProvider())
    assert rejected.provider == "none"
    assert rejected.input_quality is not None
    assert rejected.input_quality.status == REJECTED
    assert rejected.draft is None

    clarification = import_recipe_text(RecipeImportRequest(text="make food"), provider=FailingProvider())
    assert clarification.provider == "none"
    assert clarification.input_quality is not None
    assert clarification.input_quality.status == NEEDS_CLARIFICATION
    assert clarification.input_quality.clarifying_question
    assert clarification.draft is None


def test_meal_planner_vague_preferences_do_not_call_provider():
    response = create_meal_plan(MealPlanRequest(preferences="plan dinner"), provider=FailingProvider())
    assert response.provider == "none"
    assert response.selection.candidate_count == 0
    assert response.input_quality is not None
    assert response.input_quality.status == NEEDS_CLARIFICATION
    assert response.input_quality.clarifying_question == "Do you want breakfast, lunch, dinner, or a full-day plan?"


def test_dataset_search_rejects_bad_query_without_dataset_inspection(monkeypatch):
    monkeypatch.setenv("RECIPE_DATASET_DIR", "missing-private-test-path")
    response = search_dataset_recipes("!!!!!", limit=3, dataset_limit=25)

    assert response.count == 0
    assert response.input_quality is not None
    assert response.input_quality.status == REJECTED
    assert response.index.build_metadata["mode"] == "input_quality"
    assert "Configured recipe dataset directory does not exist." not in response.warnings


def test_live_eval_record_includes_input_quality_metrics():
    live_evals = load_live_eval_module()
    responses_dir = Path(".tmp-ai-demo") / "live-evals" / "input-quality-offline-test" / "responses"
    shutil.rmtree(responses_dir.parent, ignore_errors=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    def runner(_case):
        return {
            "answer": "Please add a useful ingredient.",
            "provider": "none",
            "model": "none",
            "warnings": ["Please include at least one ingredient."],
            "input_quality": {
                "status": "rejected",
                "reason": "Input is empty.",
                "clarifying_question": None,
                "warnings": ["Please include at least one ingredient."],
            },
            "retrieval": {"retrieved_count": 0},
        }

    def scorer(_workflow, _payload, _expected_model):
        return []

    try:
        record = live_evals.run_case(
            {"workflow": "ask_my_cookbook", "endpoint": "POST /ai/ask", "input_summary": "offline", "expected_checks": []},
            runner,
            responses_dir,
            "gpt-5.4-nano",
            scorer,
        )
        assert record["input_quality_status"] == "rejected"
        assert record["clarification_question_present"] is False
        assert record["provider_called"] is False
        assert record["rejected_before_provider"] is True
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


class FailingProvider(LLMProvider):
    name = "failing"
    model = "none"

    def generate_text(self, request: LLMRequest):
        raise AssertionError("Provider should not be called for deterministic input-quality responses.")

    def generate_structured(self, request: StructuredLLMRequest):
        raise AssertionError("Provider should not be called for deterministic input-quality responses.")
