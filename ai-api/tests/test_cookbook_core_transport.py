import json

from app.cookbook_core_transport import (
    CoreTransportSettings,
    LOCAL_IMAGE,
    local_core_transport_guard,
    send_core_local_commit,
)


def draft(**overrides):
    value = {
        "title": "Local Transport Soup",
        "description": "A reviewed local fixture.",
        "servings": 4,
        "ingredients": [
            {"name": "beans", "quantity": "2", "unit": "cups", "note": None},
            {"name": "lemon", "quantity": "1", "unit": "medium", "note": "zested"},
        ],
        "instructions": [
            {"step": 1, "text": "Warm the beans."},
            {"step": 2, "text": "Finish with lemon."},
        ],
        "tags": ["fixture"],
        "source": "https://example.test/fixture",
        "notes": "Reviewed local fixture.",
    }
    value.update(overrides)
    return value


def settings(**overrides):
    value = {
        "enabled": True,
        "approved": True,
        "runtime_verified": True,
        "target_url": "http://127.0.0.1:3000/",
        "image_marker": LOCAL_IMAGE,
        "compose_project": "cookbook-local",
    }
    value.update(overrides)
    return CoreTransportSettings(**value)


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def test_disabled_by_default_does_not_call_core():
    called = []
    result = send_core_local_commit(draft(), opener=lambda *_args, **_kwargs: called.append(True))

    assert result["status"] == "unavailable"
    assert result["code"] == "local_transport_blocked"
    assert called == []


def test_guard_refuses_exposed_and_deployment_contexts():
    assert "loopback_target_required" in local_core_transport_guard(settings(target_url="https://cookbook.roadmaps.link/"))
    reasons = local_core_transport_guard(settings(), env={"CI": "true"})
    assert "deployment_or_ci_context" in reasons


def test_transport_sends_only_reviewed_candidate_and_returns_safe_result():
    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({
            "status": "verified",
            "verification": "local_synthetic_auth",
            "recipe_uid": "opaque-local-uid",
            "recipe_url": "/recipe/opaque-local-uid/view",
            "read_after_write": "verified",
            "content_scope": "first_scope_no_categories_media_embeddings",
            "prompt": "must not escape",
            "absolute_path": "must not escape",
        })

    result = send_core_local_commit(
        draft(),
        idempotency_key="transport-1",
        approved=True,
        settings=settings(),
        opener=opener,
    )

    assert result == {
        "status": "verified",
        "verification": "local_synthetic_auth",
        "recipe_uid": "opaque-local-uid",
        "recipe_url": "/recipe/opaque-local-uid/view",
        "read_after_write": "verified",
        "content_scope": "first_scope_no_categories_media_embeddings",
    }
    assert captured["url"].endswith("/api/adapter/dev-only/recipes/import-candidate/verify-local-commit")
    assert captured["timeout"] == 60
    assert captured["body"]["approve_local_write"] is True
    candidate = captured["body"]["candidate"]
    assert candidate["ingredients"] == ["2 cups beans", "1 medium lemon (zested)"]
    assert candidate["instructions"] == ["Warm the beans.", "Finish with lemon."]
    assert candidate["servings"] == 4
    assert "tags" not in candidate
    assert not any(key.lower() in {"userid", "cookie", "session", "token", "prompt"} for key in candidate)


def test_confirmation_and_identity_guards_refuse_before_network():
    called = []
    opener = lambda *_args, **_kwargs: called.append(True)
    missing_confirmation = send_core_local_commit(draft(), approved=False, settings=settings(), opener=opener)
    identity = send_core_local_commit({**draft(), "userId": "sidecar"}, approved=True, settings=settings(), opener=opener)

    assert missing_confirmation["code"] == "explicit_confirmation_required"
    assert identity["code"] == "identity_assertion_rejected"
    assert called == []


def test_invalid_candidate_and_network_failure_are_safe():
    invalid = send_core_local_commit(draft(instructions=[]), approved=True, settings=settings())
    unavailable = send_core_local_commit(
        draft(),
        approved=True,
        settings=settings(),
        opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("secret path /tmp/provider-output")),
    )

    assert invalid["status"] == "invalid"
    assert invalid["code"] == "candidate_validation_failed"
    assert unavailable == {"status": "unavailable", "code": "core_transport_unavailable"}
    assert "/tmp" not in json.dumps(unavailable)
    assert "provider-output" not in json.dumps(unavailable)
