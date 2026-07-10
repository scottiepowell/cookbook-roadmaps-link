from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

from fastapi.testclient import TestClient

from evals.ai_cookbook.retrieval_eval import write_retrieval_fixture_dataset


SESSION_CASES_PATH = Path(__file__).with_name("session_cases.yaml")

PROVIDER_ENV_KEYS = (
    "AI_PROVIDER",
    "AI_MODEL",
    "AI_MAX_OUTPUT_TOKENS",
    "AI_TIMEOUT_SECONDS",
    "AI_PROVIDER_DEBUG",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_FALLBACK_MODEL",
    "OPENAI_ENABLE_LIVE_TESTS",
    "RECIPE_DATASET_DIR",
    "RECIPE_DATASET_INDEX_LIMIT",
    "AI_RETRIEVAL_CACHE_ENABLED",
    "AI_RETRIEVAL_CACHE_MAX_ENTRIES",
    "AI_RETRIEVAL_CACHE_TTL_SECONDS",
    "COOKBOOK_DB_PATH",
)

FORBIDDEN_RESPONSE_PATTERNS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    ".env",
    ".tmp-ai-demo",
    "raw prompt",
    "Creation requirements",
    "Retrieved dataset examples",
    "raw provider",
    "provider response",
    "Traceback",
    "C:\\",
    "/Users/",
    "/home/",
    "COOKBOOK_DB_PATH",
    "write_back_path",
    "cookbook_db_path",
)


@dataclass(frozen=True)
class SessionEvalResult:
    case_id: str
    passed: bool
    summary: str
    elapsed_seconds: float
    response_state: str


def load_session_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or SESSION_CASES_PATH
    cases = json.loads(case_path.read_text(encoding="utf-8"))
    for case in cases:
        case.setdefault("name", case["id"])
    return cases


def evaluate_session_case(case: dict[str, Any], dataset_dir: Path | None = None) -> SessionEvalResult:
    case_id = str(case.get("id") or case.get("name") or "recipe_session_case")
    started = monotonic()
    try:
        with _session_eval_workspace(dataset_dir) as root:
            response_state = _execute_case(case, root)
    except AssertionError as exc:
        elapsed = monotonic() - started
        return SessionEvalResult(
            case_id=case_id,
            passed=False,
            summary=f"{case_id}: {exc}",
            elapsed_seconds=elapsed,
            response_state="failed",
        )

    elapsed = monotonic() - started
    return SessionEvalResult(
        case_id=case_id,
        passed=True,
        summary=f"{case_id} state={response_state} elapsed={elapsed:.2f}s",
        elapsed_seconds=elapsed,
        response_state=response_state,
    )


def _execute_case(case: dict[str, Any], dataset_dir: Path) -> str:
    from app.main import app
    from app.recipe_session import default_recipe_session_store
    from app.retrieval_cache import reset_retrieval_cache

    case_id = str(case["id"])
    with _env_guard():
        write_retrieval_fixture_dataset(dataset_dir)
        os.environ["AI_PROVIDER"] = "mock"
        os.environ["AI_MODEL"] = "mock-basic"
        os.environ["RECIPE_DATASET_DIR"] = str(dataset_dir)
        os.environ["RECIPE_DATASET_INDEX_LIMIT"] = "5000"
        os.environ["AI_RETRIEVAL_CACHE_ENABLED"] = "true"
        os.environ["AI_RETRIEVAL_CACHE_MAX_ENTRIES"] = "128"
        os.environ["AI_RETRIEVAL_CACHE_TTL_SECONDS"] = "900"
        reset_retrieval_cache()
        default_recipe_session_store.clear()
        client = TestClient(app)
        try:
            flow = str(case["flow"])
            if flow == "start":
                final_payload = _run_start_case(client, case, dataset_dir)
            elif flow == "message":
                final_payload = _run_message_case(client, case, dataset_dir)
            elif flow == "finalize":
                final_payload = _run_finalize_case(client, case, dataset_dir)
            elif flow == "missing_session":
                final_payload = _run_missing_session_case(client, case, dataset_dir)
            else:
                raise AssertionError(f"unknown flow {flow!r}")
        finally:
            default_recipe_session_store.clear()
            reset_retrieval_cache()
    return str(final_payload.get("response_state") or final_payload.get("detail", {}).get("response_state") or "unknown")


def _run_start_case(client: TestClient, case: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    response = client.post("/ai/recipe-session/start", json={"text": case["start_text"]})
    payload = _checked_json(case["id"], response, dataset_dir)
    _assert_state(case["id"], payload, case["expected_start_state"])
    _assert_start_expectations(case, payload)
    return payload


def _run_message_case(client: TestClient, case: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    start_response = client.post("/ai/recipe-session/start", json={"text": case["start_text"]})
    start_payload = _checked_json(f"{case['id']}:start", start_response, dataset_dir)
    _assert_state(f"{case['id']}:start", start_payload, case["expected_start_state"])
    if case.get("expect_no_start_draft"):
        assert start_payload.get("draft") is None, f"{case['id']}: start emitted draft before clarification"
    interaction_id = start_payload.get("interaction_id")
    assert interaction_id, f"{case['id']}: missing interaction_id"

    message_response = client.post(
        f"/ai/recipe-session/{interaction_id}/message",
        json={"text": case["message_text"]},
    )
    payload = _checked_json(f"{case['id']}:message", message_response, dataset_dir)
    assert payload.get("response_state") in case["expected_message_states"], (
        f"{case['id']}: response_state={payload.get('response_state')!r} expected {case['expected_message_states']}"
    )
    _assert_message_expectations(case, payload)
    get_response = client.get(f"/ai/recipe-session/{interaction_id}")
    _checked_json(f"{case['id']}:get", get_response, dataset_dir)
    return payload


def _run_finalize_case(client: TestClient, case: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    start_response = client.post("/ai/recipe-session/start", json={"text": case["start_text"]})
    start_payload = _checked_json(f"{case['id']}:start", start_response, dataset_dir)
    _assert_state(f"{case['id']}:start", start_payload, case["expected_start_state"])
    interaction_id = start_payload.get("interaction_id")
    assert interaction_id, f"{case['id']}: missing interaction_id"

    finalize_response = client.post(f"/ai/recipe-session/{interaction_id}/finalize", json={"format": "draft_json"})
    payload = _checked_json(f"{case['id']}:finalize", finalize_response, dataset_dir)
    _assert_state(case["id"], payload, case["expected_finalize_state"])
    if case.get("expect_demo_warning"):
        warnings = " ".join(payload.get("warnings") or []).lower()
        assert "no production cookbook write-back" in warnings, f"{case['id']}: missing demo-only finalize warning"
    return payload


def _run_missing_session_case(client: TestClient, case: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    interaction_id = case["missing_interaction_id"]
    response = client.get(f"/ai/recipe-session/{interaction_id}")
    assert response.status_code == int(case["expected_status_code"]), (
        f"{case['id']}: HTTP {response.status_code} expected {case['expected_status_code']}"
    )
    payload = _checked_json(case["id"], response, dataset_dir, expected_status=int(case["expected_status_code"]))
    detail = payload.get("detail") or {}
    assert detail.get("response_state") == case["expected_response_state"], (
        f"{case['id']}: response_state={detail.get('response_state')!r} expected {case['expected_response_state']!r}"
    )
    message_response = client.post(f"/ai/recipe-session/{interaction_id}/message", json={"text": "thanks"})
    message_payload = _checked_json(f"{case['id']}:message", message_response, dataset_dir, expected_status=404)
    assert (message_payload.get("detail") or {}).get("response_state") == case["expected_response_state"]
    return detail


def _assert_start_expectations(case: dict[str, Any], payload: dict[str, Any]) -> None:
    if case.get("expected_confidence"):
        confidence = (payload.get("requirements") or {}).get("confidence_label")
        assert confidence in case["expected_confidence"], (
            f"{case['id']}: confidence_label={confidence!r} expected {case['expected_confidence']}"
        )
    _assert_draft_expectation(case, payload)
    _assert_citation_expectation(case, payload)
    if case.get("expected_support_not"):
        assert payload.get("support_level") != case["expected_support_not"], (
            f"{case['id']}: support_level unexpectedly {case['expected_support_not']!r}"
        )
    if case.get("expect_clarification"):
        assert payload.get("clarification_question"), f"{case['id']}: missing clarification question"
        assert len((payload.get("requirements") or {}).get("open_questions") or []) == 1
    else:
        assert not payload.get("clarification_question"), f"{case['id']}: unexpected clarification question"


def _assert_message_expectations(case: dict[str, Any], payload: dict[str, Any]) -> None:
    if "expect_rag_refreshed" in case:
        assert payload.get("rag_refreshed") is bool(case["expect_rag_refreshed"]), (
            f"{case['id']}: rag_refreshed={payload.get('rag_refreshed')!r}"
        )
    expected_changed_fields = case.get("expected_changed_fields")
    if expected_changed_fields is not None:
        assert payload.get("changed_fields") == expected_changed_fields, (
            f"{case['id']}: changed_fields={payload.get('changed_fields')!r} expected {expected_changed_fields!r}"
        )
    expected_delta_label = case.get("expected_delta_label")
    if expected_delta_label:
        assert (payload.get("decision") or {}).get("delta_label") == expected_delta_label, (
            f"{case['id']}: delta_label={(payload.get('decision') or {}).get('delta_label')!r}"
        )
    expected_delta_labels = case.get("expected_delta_labels")
    if expected_delta_labels:
        assert (payload.get("decision") or {}).get("delta_label") in expected_delta_labels, (
            f"{case['id']}: delta_label={(payload.get('decision') or {}).get('delta_label')!r}"
        )
    for field, expected in (case.get("expected_requirement_contains") or {}).items():
        value = ((payload.get("requirements") or {}).get(field) or {}).get("value") or ""
        assert expected in value, f"{case['id']}: requirements.{field}={value!r} missing {expected!r}"
    _assert_draft_expectation(case, payload)


def _assert_draft_expectation(case: dict[str, Any], payload: dict[str, Any]) -> None:
    if case.get("expect_draft"):
        assert payload.get("draft"), f"{case['id']}: missing draft"
        assert payload.get("draft_summary"), f"{case['id']}: missing draft_summary"
    elif case.get("expect_draft") is False:
        assert payload.get("draft") is None, f"{case['id']}: unexpected draft"


def _assert_citation_expectation(case: dict[str, Any], payload: dict[str, Any]) -> None:
    citations = payload.get("citations") or []
    if case.get("expect_citations"):
        assert citations, f"{case['id']}: missing citations"
        assert all(citation.get("id") for citation in citations), f"{case['id']}: citation missing id"
    elif case.get("expect_citations") is False:
        assert citations == [], f"{case['id']}: unexpected citations"


def _assert_state(label: str, payload: dict[str, Any], expected: str) -> None:
    assert payload.get("response_state") == expected, (
        f"{label}: response_state={payload.get('response_state')!r} expected {expected!r}"
    )


def _checked_json(
    label: str,
    response: Any,
    dataset_dir: Path,
    *,
    expected_status: int = 200,
) -> dict[str, Any]:
    assert response.status_code == expected_status, f"{label}: HTTP {response.status_code}: {response.text}"
    payload = response.json()
    _assert_safe_response(label, response.text, dataset_dir)
    return payload


def _assert_safe_response(label: str, text: str, dataset_dir: Path) -> None:
    assert str(dataset_dir) not in text, f"{label}: leaked generated dataset path"
    for pattern in FORBIDDEN_RESPONSE_PATTERNS:
        assert pattern not in text, f"{label}: leaked forbidden pattern {pattern!r}"


class _env_guard:
    def __init__(self) -> None:
        self._old_env: dict[str, str | None] = {}

    def __enter__(self) -> None:
        self._old_env = {key: os.environ.get(key) for key in PROVIDER_ENV_KEYS}
        for key in PROVIDER_ENV_KEYS:
            os.environ.pop(key, None)

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class _session_eval_workspace:
    def __init__(self, dataset_dir: Path | None = None) -> None:
        self.path = dataset_dir or Path(".tmp-pytest-evals") / f"session-eval-{uuid.uuid4().hex}"

    def __enter__(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None
