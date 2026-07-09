from app.rag_support_policy import (
    SUPPORT_MODERATE,
    SUPPORT_NONE,
    SUPPORT_STRONG,
    SUPPORT_WEAK,
    assess_importer_rag_support,
)


SECRET_MARKERS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization:",
    ".env",
    "CLOUDFLARE_TUNNEL_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
)


def test_support_policy_classifies_strong_support():
    assessment = assess_importer_rag_support(
        relevance_category="strong",
        retrieved_count=3,
        citation_count=3,
        packed_count=2,
        weak_examples_included=False,
        matched_result_scores=[120, 84, 30],
        warning=None,
        top_k_relevant_count=2,
    )

    assert assessment.support_level == SUPPORT_STRONG
    assert assessment.should_claim_rag_grounded is True
    assert assessment.should_show_weak_support_warning is False
    assert assessment.strong_citation_count >= 1
    assert assessment.citation_support_count >= 1
    assert "strong" in assessment.support_message.lower()


def test_support_policy_classifies_moderate_support():
    assessment = assess_importer_rag_support(
        relevance_category="moderate",
        retrieved_count=3,
        citation_count=3,
        packed_count=2,
        weak_examples_included=False,
        matched_result_scores=[60, 42, 18],
        warning=None,
        top_k_relevant_count=2,
    )

    assert assessment.support_level == SUPPORT_MODERATE
    assert assessment.should_claim_rag_grounded is False
    assert assessment.should_show_weak_support_warning is False
    assert assessment.citation_support_count >= 1
    assert "moderate" in assessment.support_message.lower()


def test_support_policy_classifies_weak_support():
    assessment = assess_importer_rag_support(
        relevance_category="weak",
        retrieved_count=2,
        citation_count=2,
        packed_count=1,
        weak_examples_included=True,
        matched_result_scores=[18, 9],
        warning="Retrieved examples were weak matches; recipe draft was primarily shaped by user-provided notes and general recipe structure.",
        top_k_relevant_count=0,
    )

    assert assessment.support_level == SUPPORT_WEAK
    assert assessment.should_claim_rag_grounded is False
    assert assessment.should_show_weak_support_warning is True
    assert assessment.citation_support_count == 0
    assert "weak" in assessment.support_message.lower()


def test_support_policy_classifies_none_support():
    assessment = assess_importer_rag_support(
        relevance_category="unavailable",
        retrieved_count=0,
        citation_count=0,
        packed_count=0,
        weak_examples_included=False,
        matched_result_scores=[],
        warning="Importer dataset RAG examples were unavailable; created the draft from user notes only.",
        top_k_relevant_count=None,
    )

    assert assessment.support_level == SUPPORT_NONE
    assert assessment.should_claim_rag_grounded is False
    assert assessment.should_show_weak_support_warning is True
    assert assessment.citation_support_count == 0
    assert "no useful dataset examples" in assessment.support_message.lower()


def test_support_policy_messages_stay_safe_and_concise():
    assessment = assess_importer_rag_support(
        relevance_category="strong",
        retrieved_count=1,
        citation_count=1,
        packed_count=1,
        weak_examples_included=False,
        matched_result_scores=[50],
        warning=None,
        top_k_relevant_count=1,
    )

    serialized = assessment.support_message + " " + assessment.support_reason
    assert len(assessment.support_message) <= 220
    assert len(assessment.support_reason) <= 220
    for marker in SECRET_MARKERS:
        assert marker not in serialized
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized

