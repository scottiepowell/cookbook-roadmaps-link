from __future__ import annotations

from dataclasses import dataclass

from app.dataset_index import WEAK_MATCH_SCORE_THRESHOLD


SUPPORT_STRONG = "strong"
SUPPORT_MODERATE = "moderate"
SUPPORT_WEAK = "weak"
SUPPORT_NONE = "none"

_STRONG_SCORE_THRESHOLD = int(WEAK_MATCH_SCORE_THRESHOLD * 1.5)

_SUPPORT_MESSAGES = {
    SUPPORT_STRONG: (
        "Dataset support is strong: retrieved examples closely match the dish intent and inform structure, proportions, and step completeness."
    ),
    SUPPORT_MODERATE: (
        "Dataset support is moderate: retrieved examples are related, but your notes still drive the recipe."
    ),
    SUPPORT_WEAK: (
        "Dataset support is weak: retrieved examples are broad, so the draft relies mainly on your notes and disclosed estimates."
    ),
    SUPPORT_NONE: (
        "No useful dataset examples were available; the draft was generated from your notes, defaults, and disclosed assumptions."
    ),
}


@dataclass(frozen=True)
class RagSupportAssessment:
    support_level: str
    support_reason: str
    citation_support_count: int
    weak_citation_count: int
    strong_citation_count: int
    support_message: str
    should_claim_rag_grounded: bool
    should_show_weak_support_warning: bool


def assess_importer_rag_support(
    *,
    relevance_category: str | None,
    retrieved_count: int,
    citation_count: int,
    packed_count: int,
    weak_examples_included: bool,
    matched_result_scores: list[int] | None = None,
    warning: str | None = None,
    top_k_relevant_count: int | None = None,
    anchor_coverage: str | None = None,
) -> RagSupportAssessment:
    scores = [int(score) for score in matched_result_scores or []]
    strong_citation_count = sum(1 for score in scores if score >= _STRONG_SCORE_THRESHOLD)
    moderate_citation_count = sum(1 for score in scores if WEAK_MATCH_SCORE_THRESHOLD <= score < _STRONG_SCORE_THRESHOLD)
    weak_citation_count = max(0, citation_count - strong_citation_count - moderate_citation_count)

    if retrieved_count <= 0 or citation_count <= 0 or packed_count <= 0 or relevance_category in {None, "", "unavailable"}:
        support_level = SUPPORT_NONE
        support_reason = "No useful retrieved examples were available."
        citation_support_count = 0
        weak_citation_count = max(weak_citation_count, citation_count)
    elif relevance_category == SUPPORT_STRONG and strong_citation_count > 0 and not weak_examples_included and not warning:
        support_level = SUPPORT_STRONG
        citation_support_count = strong_citation_count + moderate_citation_count
        support_reason = _strong_reason(strong_citation_count, top_k_relevant_count, anchor_coverage)
    elif relevance_category in {SUPPORT_STRONG, SUPPORT_MODERATE} and (strong_citation_count > 0 or moderate_citation_count > 0):
        support_level = SUPPORT_MODERATE
        citation_support_count = strong_citation_count + moderate_citation_count
        support_reason = _moderate_reason(citation_support_count, top_k_relevant_count, anchor_coverage)
    else:
        support_level = SUPPORT_WEAK
        citation_support_count = 0
        support_reason = warning or "Retrieved examples were broad structure-only matches."

    support_message = _SUPPORT_MESSAGES[support_level]
    should_claim_rag_grounded = support_level == SUPPORT_STRONG
    should_show_weak_support_warning = support_level in {SUPPORT_WEAK, SUPPORT_NONE}
    return RagSupportAssessment(
        support_level=support_level,
        support_reason=support_reason,
        citation_support_count=citation_support_count,
        weak_citation_count=weak_citation_count,
        strong_citation_count=strong_citation_count,
        support_message=support_message,
        should_claim_rag_grounded=should_claim_rag_grounded,
        should_show_weak_support_warning=should_show_weak_support_warning,
    )


def _strong_reason(
    strong_citation_count: int,
    top_k_relevant_count: int | None,
    anchor_coverage: str | None,
) -> str:
    parts = [f"{strong_citation_count} strong match(es)"]
    if top_k_relevant_count is not None:
        parts.append(f"{top_k_relevant_count} relevant in top-k")
    if anchor_coverage:
        parts.append(f"anchors {anchor_coverage}")
    return ", ".join(parts) + "."


def _moderate_reason(
    citation_support_count: int,
    top_k_relevant_count: int | None,
    anchor_coverage: str | None,
) -> str:
    parts = [f"{citation_support_count} related example(s)"]
    if top_k_relevant_count is not None:
        parts.append(f"{top_k_relevant_count} relevant in top-k")
    if anchor_coverage:
        parts.append(f"anchors {anchor_coverage}")
    return ", ".join(parts) + "."
