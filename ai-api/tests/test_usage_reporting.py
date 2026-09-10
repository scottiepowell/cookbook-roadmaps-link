import json
from contextlib import closing
from types import SimpleNamespace

import httpx
import pytest

from app.usage_reporting import build_report, connect, record_usage, send_report
from app.providers.openai_provider import OpenAIProvider
from app.providers.base import LLMRequest, StructuredLLMRequest
from app.providers.errors import ProviderCallError


@pytest.fixture
def reporting(tmp_path, monkeypatch):
    path = str(tmp_path / "usage.sqlite3")
    monkeypatch.setenv("AI_USAGE_DB_PATH", path)
    monkeypatch.setenv("AI_REPORT_EMAIL_ENABLED", "true")
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("AI_REPORT_FROM", "reports@example.test")
    monkeypatch.setenv("AI_REPORT_TO", "operator@example.test")
    record_usage("test-model", {"input_tokens": 10, "output_tokens": 5}, "completed")
    return path


def report(path):
    return build_report(path, "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z")


def test_durable_actual_usage_and_unknown_failure(reporting):
    record_usage("test-model", None, "failed")
    assert report(reporting)["models"] == [{
        "model": "test-model", "calls": 2, "failures": 1,
        "calls_missing_usage": 1, "input_tokens": 10,
        "output_tokens": 5, "total_tokens": 15,
    }]
    with closing(connect(reporting)) as db:
        db.execute("UPDATE usage_events SET occurred_at='2026-09-10T00:00:00+00:00'")
        db.commit()
    assert build_report(reporting, "2026-09-09T00:00:00Z", "2026-09-10T00:00:00Z")["models"] == []
    assert build_report(reporting, "2026-09-10T00:00:00Z", "2026-09-11T00:00:00Z")["models"][0]["calls"] == 2


def test_report_requires_existing_coverage_and_timezone(tmp_path, reporting):
    with pytest.raises(ValueError, match="not initialized"):
        report(str(tmp_path / "absent.sqlite3"))
    with pytest.raises(ValueError, match="timezone"):
        build_report(reporting, "2026-09-09", "2026-09-10")


def test_storage_failure_does_not_break_generation(monkeypatch, caplog, tmp_path):
    monkeypatch.setenv("AI_USAGE_DB_PATH", str(tmp_path))
    record_usage("test-model", None, "failed")
    assert "usage_record_failed" in caplog.text
    assert str(tmp_path) not in caplog.text


def test_send_disabled_by_default(reporting, monkeypatch):
    monkeypatch.delenv("AI_REPORT_EMAIL_ENABLED")
    with pytest.raises(ValueError, match="disabled"):
        send_report(reporting, report(reporting))


def test_accepted_report_never_resends_after_restart(reporting):
    requests = []
    def send(request):
        requests.append(request)
        assert request.url == "https://api.resend.com/emails"
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"id": "test-message"})
    transport = httpx.MockTransport(send)
    assert send_report(reporting, report(reporting), transport=transport, now=100) == "accepted"
    assert send_report(reporting, report(reporting), transport=transport, now=999999) == "already_accepted"
    assert len(requests) == 1


def test_uncertain_delivery_retries_frozen_payload_and_expires(reporting):
    requests = []
    def timeout(request):
        requests.append(request)
        raise httpx.ReadTimeout("sensitive provider diagnostics")
    transport = httpx.MockTransport(timeout)
    for when in (100, 200):
        with pytest.raises(ValueError, match="unconfirmed") as exc:
            send_report(reporting, report(reporting), transport=transport, now=when)
        assert "sensitive" not in str(exc.value)
        record_usage("test-model", {"input_tokens": 99}, "completed")
    assert requests[0].content == requests[1].content
    assert requests[0].headers["idempotency-key"] == requests[1].headers["idempotency-key"]
    with pytest.raises(ValueError, match="reconcile"):
        send_report(reporting, report(reporting), transport=transport, now=100 + 23 * 3600)
    assert len(requests) == 2


@pytest.mark.parametrize("status", [401, 429, 500])
def test_provider_rejection_is_not_success(reporting, status):
    with pytest.raises(ValueError, match="unconfirmed"):
        send_report(reporting, report(reporting), transport=httpx.MockTransport(
            lambda request: httpx.Response(status, json={"message": "private detail"})
        ))
    with closing(connect(reporting)) as db:
        assert db.execute("SELECT accepted FROM report_delivery").fetchone()[0] == 0


def test_provider_hooks_count_invalid_json_tokens(reporting):
    provider = OpenAIProvider(api_key="test")
    response = SimpleNamespace(output_text="{", usage=SimpleNamespace(input_tokens=4, output_tokens=2, total_tokens=6))
    provider._client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: response))
    with pytest.raises(ProviderCallError):
        provider.generate_structured(StructuredLLMRequest(prompt="private prompt", schema_name="test", schema={}))
    provider.generate_text(LLMRequest(prompt="private prompt"))
    result = report(reporting)
    model = next(row for row in result["models"] if row["model"] == provider.model)
    assert model["calls"] == 2
    assert model["failures"] == 1
    assert model["total_tokens"] == 12
    assert "private prompt" not in json.dumps(result)
