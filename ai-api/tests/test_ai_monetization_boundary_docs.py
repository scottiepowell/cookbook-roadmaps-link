from __future__ import annotations

from pathlib import Path


FORBIDDEN_STRINGS = (
    "sk_live_",
    "sk_test_",
    "STRIPE_SECRET_KEY",
    "PAYPAL_CLIENT_SECRET",
    "checkout_session_secret",
    "webhook_secret",
    "Authorization: Bearer real",
    "OPENAI_API_KEY",
    ".env",
    "C:\\Users\\",
    "/home/",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_monetization_boundary_adr_exists_and_states_near_term_model():
    adr = Path("docs/ai-monetization-and-entitlement-boundary-adr.md")
    assert adr.exists()
    text = _read(adr)
    assert "ads" in text.lower()
    assert "sponsorship" in text.lower()
    assert "partner placements" in text.lower()
    assert "paid access is not being implemented now" in text.lower()
    assert "separate ADR" in text
    assert "EntitlementPlan" in text
    assert "EntitlementFeature" in text
    assert "RevenueChannel" in text
    assert "SponsorPlacement" in text
    assert "AdPlacement" in text
    assert "AffiliateDisclosure" in text


def test_monetization_boundary_adr_is_secret_free_and_not_runtime_payment_instructions():
    text = _read(Path("docs/ai-monetization-and-entitlement-boundary-adr.md"))
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in text
    assert "set up stripe" not in text.lower()
    assert "configure paypal" not in text.lower()
    assert "enable checkout" not in text.lower()


def test_repo_references_new_adr_title():
    backlog = _read(Path("docs/ai-implementation-backlog.md"))
    feature_status = _read(Path("docs/ai-feature-status.md"))
    readme = _read(Path("README.md"))
    assert "0029I: Monetization And Entitlement Boundary ADR" in backlog
    assert "Monetization And Entitlement Boundary ADR" in feature_status
    assert "Monetization And Entitlement Boundary ADR" in readme


def test_updated_docs_remind_that_monetization_is_separate_from_access_and_budget():
    public_route_review = _read(Path("docs/ai-public-route-exposure-review.md"))
    schema = _read(Path("docs/ai-session-metering-schema.md"))
    budget = _read(Path("docs/ai-provider-budget-enforcement.md"))
    invite = _read(Path("docs/ai-invite-only-demo-session-flow.md"))
    usage = _read(Path("docs/ai-admin-usage-report-prototype.md"))
    live_runbook = _read(Path("docs/ai-live-demo-runbook.md"))

    assert "monetization" in public_route_review.lower()
    assert "entitlement" in schema.lower()
    assert "monetization" in budget.lower()
    assert "entitlement" in invite.lower()
    assert "billing" in usage.lower()
    assert "monetization" in live_runbook.lower()
