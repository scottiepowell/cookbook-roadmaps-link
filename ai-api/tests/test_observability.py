import json
import logging

from fastapi.testclient import TestClient

from app.main import app
from app.observability import LOGGER_NAME, log_ai_workflow


def test_request_logging_middleware_emits_safe_fields(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    response = TestClient(app).get("/health", headers={"x-request-id": "demo-request-1"})

    assert response.status_code == 200
    events = [json.loads(record.message) for record in caplog.records if record.name == LOGGER_NAME]
    request_events = [event for event in events if event["event"] == "ai.request"]
    assert request_events
    event = request_events[-1]
    assert event["request_id"] == "demo-request-1"
    assert event["endpoint_name"] == "/health"
    assert event["status"] == 200
    assert "duration_ms" in event
    assert "OPENAI_API_KEY" not in record_messages(caplog)
    assert "Authorization:" not in record_messages(caplog)


def test_workflow_logging_helper_emits_counts_without_payloads(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    log_ai_workflow(
        "dataset.ask",
        provider="mock",
        model="mock-basic",
        retrieved_count=2,
        citation_count=2,
        warning_count=1,
    )

    events = [json.loads(record.message) for record in caplog.records if record.name == LOGGER_NAME]
    event = events[-1]
    assert event["event"] == "ai.workflow"
    assert event["endpoint_name"] == "dataset.ask"
    assert event["provider"] == "mock"
    assert event["model"] == "mock-basic"
    assert event["retrieved_count"] == 2
    assert event["citation_count"] == 2
    assert event["warning_count"] == 1
    assert "prompt" not in event
    assert "response_body" not in event


def record_messages(caplog):
    return "\n".join(record.message for record in caplog.records)
