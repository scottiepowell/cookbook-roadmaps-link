from __future__ import annotations

import subprocess
import sys
from pathlib import Path


FORBIDDEN_STRINGS = (
    "sk" + "-proj-",
    "sk" + "_live_",
    "sk" + "_test_",
    "glm" + "-key",
    "OPENAI_API_KEY",
    "Authorization: Bearer real",
    ".env",
    "C:" + "\\Users" + "\\",
    "/" + "home" + "/",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_fact_register_and_gate_docs_exist_and_keep_glm_blocked():
    register = Path("docs/ai-secondary-provider-fact-register.md")
    gate = Path("docs/ai-secondary-provider-implementation-gate.md")
    assert register.exists()
    assert gate.exists()

    register_text = _read(register)
    gate_text = _read(gate)
    lowered = register_text.lower()

    assert "Provider candidate: GLM" in register_text
    assert "Candidate model: GLM-4.7 Flash" in register_text
    assert "Current implementation status: not implemented" in register_text
    assert "verification_status: unverified" in register_text
    assert "implementation_gate: blocked" in register_text
    assert "primary provider documentation was not available in this task" in register_text
    assert "runtime adapter work is blocked" in lowered
    assert "runtime adapter work requires a separate future mailbox task" in gate_text


def test_fact_register_does_not_claim_verified_glm_facts_without_sources():
    text = _read(Path("docs/ai-secondary-provider-fact-register.md"))
    lowered = text.lower()
    for required in (
        "primary_documentation_references",
        "api_protocol_and_auth",
        "pricing_input_tokens",
        "pricing_output_tokens",
        "privacy_policy",
        "data_retention_policy",
        "training_data_use_policy",
        "regional_availability",
        "error_response_shape",
    ):
        assert required in text
    assert "verified pricing" not in lowered
    assert "verified privacy" not in lowered
    assert "verified api behavior" not in lowered
    assert "unknown" in lowered
    assert "unverified" in lowered


def test_gate_docs_keep_final_answer_generation_and_private_recipe_data_blocked():
    combined = "\n".join(
        [
            _read(Path("docs/ai-secondary-provider-fact-register.md")),
            _read(Path("docs/ai-secondary-provider-implementation-gate.md")),
            _read(Path("docs/ai-secondary-provider-offload-adr.md")),
        ]
    ).lower()
    assert "final_user_answer_generation" in combined
    assert "private_user_recipe_data_processing_without_explicit_future_privacy_decision" in combined
    assert "blocked" in combined
    assert "openai `gpt-5.4-nano`" in combined


def test_fact_gate_fixture_and_runner_exist_and_pass_offline():
    cases_path = Path("evals/ai_cookbook/secondary_provider_fact_gate.yaml")
    runner_path = Path("evals/ai_cookbook/secondary_provider_fact_gate_eval.py")
    assert cases_path.exists()
    assert runner_path.exists()

    cases_text = _read(cases_path)
    for case_id in (
        "glm_candidate_unverified_blocked",
        "synthetic_fully_verified_safe_candidate",
        "candidate_missing_privacy_policy",
        "candidate_missing_pricing",
        "candidate_allows_blocked_task_class",
        "candidate_final_answer_generation_not_blocked",
        "candidate_missing_fallback_behavior",
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
    assert "Secondary provider fact gate eval passed" in result.stdout
    assert "FAIL:" not in result.stdout
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in result.stdout
        assert forbidden not in result.stderr


def test_runtime_app_files_do_not_add_glm_runtime_code_or_secondary_routing():
    app_dir = Path("ai-api/app")
    app_text = "\n".join(path.read_text(encoding="utf-8") for path in app_dir.rglob("*.py"))
    lowered = app_text.lower()
    assert "glm-4.7-flash" not in lowered
    assert "ai_secondary_provider_enabled" not in lowered
    assert "ai_secondary_provider" not in lowered
    assert "secondary provider" not in lowered


def test_repo_docs_reference_0031b_and_preserve_0030p_baseline():
    backlog = _read(Path("docs/ai-implementation-backlog.md"))
    status = _read(Path("docs/ai-feature-status.md"))
    evals_plan = _read(Path("docs/ai-evals-plan.md"))
    readme = _read(Path("README.md"))

    assert "0031B: Secondary Provider Fact Verification And Implementation Gate" in backlog
    assert "0030P" in backlog
    assert "0031B adds provider fact verification and implementation gating" in evals_plan
    assert "runtime adapter work remains blocked" in evals_plan.lower()
    assert "secondary provider fact register" in status.lower()
    assert "0030P" in readme
    assert "ai-secondary-provider-fact-register.md" in readme
    assert "ai-secondary-provider-implementation-gate.md" in readme


def test_new_docs_are_secret_free():
    combined = "\n".join(
        _read(path)
        for path in (
            Path("docs/ai-secondary-provider-fact-register.md"),
            Path("docs/ai-secondary-provider-implementation-gate.md"),
            Path("evals/ai_cookbook/secondary_provider_fact_gate.yaml"),
            Path("outbox/0031B-secondary-provider-fact-verification-and-implementation-gate-results.md")
            if Path("outbox/0031B-secondary-provider-fact-verification-and-implementation-gate-results.md").exists()
            else Path("docs/ai-secondary-provider-fact-register.md"),
        )
    )
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in combined
