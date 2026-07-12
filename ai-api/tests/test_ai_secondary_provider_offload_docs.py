from __future__ import annotations

import subprocess
import sys
from pathlib import Path


FORBIDDEN_STRINGS = (
    "sk" + "-proj-",
    "sk" + "_live_",
    "sk" + "_test_",
    "glm" + "-key",
    "raw_" + "provider_prompt",
    "raw_" + "provider_response",
    "C:" + "\\Users" + "\\",
    "/" + "home" + "/",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_secondary_provider_adr_exists_and_sets_disabled_docs_only_boundary():
    adr = Path("docs/ai-secondary-provider-offload-adr.md")
    assert adr.exists()
    text = _read(adr)
    lowered = text.lower()
    assert "GLM-4.7 Flash" in text
    assert "disabled by default" in lowered
    assert "runtime integration is not implemented" in lowered
    assert "candidate provider name" in lowered
    assert "gpt-5.4-nano" in text
    assert "final-answer provider" in lowered
    assert "openai `gpt-5.4-nano` path" in lowered
    assert "advisory inputs" in lowered
    assert "must not be delegated" in lowered


def test_secondary_provider_adr_includes_allowed_blocked_and_policy_sections():
    text = _read(Path("docs/ai-secondary-provider-offload-adr.md"))
    for section in (
        "## Status",
        "## Context",
        "## Decision",
        "## Allowed Offload Task Classes",
        "## Blocked Task Classes",
        "## Privacy And Data-Boundary Policy",
        "## Budget And Usage-Reporting Policy",
        "## Fallback And Failure Behavior",
        "## Evaluation Plan",
        "## Future Implementation Gates",
        "## Non-Goals",
    ):
        assert section in text
    for required in (
        "query_expansion",
        "ingredient_synonym_expansion",
        "dataset_metadata_cleanup_suggestions",
        "title_or_slug_suggestions",
        "non_final_clarification_candidate_generation",
        "context_compression",
        "draft_critique_against_quality_checklist",
        "formatting_only_rewrites_where_factual_content_is_already_fixed",
        "final_user_answer_generation",
        "final_recipe_draft_generation",
        "provider_budget_decisions",
        "invite_session_security_decisions",
    ):
        assert required in text


def test_secondary_provider_docs_are_secret_free_and_do_not_claim_runtime_glm_integration():
    paths = [
        Path("docs/ai-secondary-provider-offload-adr.md"),
        Path("docs/ai-evals-plan.md"),
        Path("docs/ai-feature-status.md"),
        Path("docs/ai-implementation-backlog.md"),
        Path("README.md"),
    ]
    combined = "\n".join(_read(path) for path in paths)
    lowered = combined.lower()
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in combined
    assert "install glm sdk" not in lowered
    assert "make glm api calls" not in lowered
    assert "automatic model fallback" not in lowered


def test_eval_cases_and_runner_exist_and_run_offline():
    cases_path = Path("evals/ai_cookbook/secondary_provider_offload_cases.yaml")
    runner_path = Path("evals/ai_cookbook/secondary_provider_offload_eval.py")
    assert cases_path.exists()
    assert runner_path.exists()
    cases_text = _read(cases_path)
    for case_id in (
        "good_query_expansion",
        "bad_query_expansion_unrelated_terms",
        "good_context_compression_preserves_citation_ids",
        "bad_context_compression_invents_or_drops_citation_ids",
        "good_title_slug_suggestions_grounded",
        "bad_title_slug_suggestions_unsupported_claims",
        "good_clarification_candidates_useful",
        "bad_clarification_candidates_private_data_request",
        "good_draft_critique_catches_quality_issue",
        "bad_draft_critique_becomes_final_answer",
    ):
        assert case_id in cases_text

    result = subprocess.run(
        [sys.executable, str(runner_path)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "Secondary provider offload eval passed" in result.stdout
    assert "FAIL:" not in result.stdout
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in result.stdout
        assert forbidden not in result.stderr


def test_runtime_app_files_do_not_add_secondary_provider_routing():
    app_dir = Path("ai-api/app")
    app_text = "\n".join(path.read_text(encoding="utf-8") for path in app_dir.rglob("*.py"))
    lowered = app_text.lower()
    assert "glm-4.7-flash" not in lowered
    assert "ai_secondary_provider" not in lowered
    assert "secondary provider" not in lowered


def test_repo_docs_reference_the_new_adr_and_offline_eval_harness():
    backlog = _read(Path("docs/ai-implementation-backlog.md"))
    feature_status = _read(Path("docs/ai-feature-status.md"))
    evals_plan = _read(Path("docs/ai-evals-plan.md"))
    readme = _read(Path("README.md"))

    assert "0031A: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness" in backlog
    assert "Secondary provider offload ADR" in feature_status or "secondary provider offload ADR" in feature_status.lower()
    assert "secondary_provider_offload_eval.py" in evals_plan
    assert "ai-secondary-provider-offload-adr.md" in readme
