import os
import uuid
from pathlib import Path

from evals.ai_cookbook import session_eval


EXPECTED_CASE_IDS = [
    "detailed_cheesecake_generates_draft",
    "vague_dessert_clarifies",
    "no_bake_refreshes_rag",
    "carbonara_chatter_no_refresh",
    "omelet_formatting_no_refresh",
    "clarification_answer_generates_draft",
    "air_fryer_followup_refreshes_rag",
    "excluded_ingredient_followup_refreshes_rag",
    "finalize_demo_only",
    "finalize_without_draft_stays_clarification",
    "missing_session_safe",
]


def test_session_eval_cases_load_and_are_named():
    cases = session_eval.load_session_cases()

    assert [case["id"] for case in cases] == EXPECTED_CASE_IDS
    assert all(case["name"] == case["id"] for case in cases)
    assert {case["flow"] for case in cases} == {"start", "message", "finalize", "missing_session"}


def test_session_eval_harness_passes_with_generated_fixture_data():
    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    dataset_root = base / f"session-harness-{uuid.uuid4().hex}"
    cases = session_eval.load_session_cases()

    results = [
        session_eval.evaluate_session_case(case, dataset_dir=dataset_root / case["id"])
        for case in cases
    ]

    assert all(result.passed for result in results)
    assert [result.case_id for result in results] == EXPECTED_CASE_IDS
    assert all("elapsed=" in result.summary for result in results)
    assert results[0].response_state == "draft_generated"
    assert results[1].response_state == "clarification_needed"
    assert results[-1].response_state == "not_found"


def test_session_eval_harness_reports_case_id_and_expected_state_on_failure():
    case = session_eval.load_session_cases()[0].copy()
    case["expected_start_state"] = "clarification_needed"
    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    dataset_root = base / f"session-harness-failure-{uuid.uuid4().hex}"

    result = session_eval.evaluate_session_case(case, dataset_dir=dataset_root)

    assert result.passed is False
    assert case["id"] in result.summary
    assert "expected 'clarification_needed'" in result.summary
    assert "response_state='draft_generated'" in result.summary


def test_session_eval_harness_does_not_require_live_provider_settings(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_ENABLE_LIVE_TESTS", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-session-eval-secret")
    case = session_eval.load_session_cases()[1]
    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    dataset_root = base / f"session-harness-env-{uuid.uuid4().hex}"

    result = session_eval.evaluate_session_case(case, dataset_dir=dataset_root)

    assert result.passed is True
    assert os.environ["AI_PROVIDER"] == "openai"
    assert os.environ["OPENAI_API_KEY"] == "sk-fake-session-eval-secret"
