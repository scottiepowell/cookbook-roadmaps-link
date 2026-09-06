from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json

from fastapi import APIRouter, HTTPException, Request

from app.ai_access_models import AiAccessWorkflow
from app.ai_mode_routing import resolve_ai_mode
from app.ai_invite_sessions import require_demo_workflow_access
from app.importer import RecipeImportProviderError, RecipeImportValidationError, import_recipe_text
from app.observability import log_ai_workflow
from app.providers.errors import extract_provider_debug_details
from app.recipe_requirements import (
    RecipeClarificationQuestion,
    RecipeFollowUpClassification,
    RecipeFollowUpLabel,
    RecipeRequirementField,
    RecipeRequirementSource,
    RecipeRequirementsState,
    RecipeResolvedQuestion,
    RecipeRetrievalSummary,
    RecipeSessionDecision,
    RecipeSessionResponseState,
    classify_follow_up,
    decide_clarification,
    decide_rag_refresh,
    extract_recipe_requirements,
    suggests_new_recipe,
)
from app.recipe_scaling import (
    draft_contains_ingredient,
    is_additive_serving_change,
    is_serving_only_change,
    requested_serving_count,
    scale_additive_recipe_draft,
    scale_recipe_draft,
)
from app.recipe_session import (
    RecipeSessionState,
    build_requirement_diff,
    build_revision_summary,
    default_recipe_start_idempotency_store,
    default_recipe_session_store,
)
from app.recipe_revision_guard import validate_recipe_revision
from app.schemas import (
    RecipeImportDraft,
    RecipeImportRequest,
    RecipeRequirementValueResponse,
    RecipeSessionApiResponse,
    RecipeSessionDecisionResponse,
    RecipeSessionDraftSummary,
    RecipeSessionRequirementDiffResponse,
    RecipeSessionFinalizeRequest,
    RecipeSessionMessageRequest,
    RecipeSessionRequirementsResponse,
    RecipeSessionRetrievalSummary,
    RecipeSessionStartRequest,
)


router = APIRouter(prefix="/ai/recipe-session", tags=["recipe-session-alpha"])
MAX_RECIPE_CHANGES = 10


def _resolve_session_provider(payload):
    if payload.provider_mode is None and payload.model is None:
        return None
    resolution = resolve_ai_mode(payload.provider_mode, payload.model)
    if resolution.effective_provider is None:
        raise HTTPException(status_code=503, detail=resolution.safe_unavailable_reason or "Requested AI mode is unavailable.")
    return resolution.provider()


@router.post("/start", response_model=RecipeSessionApiResponse)
def start_recipe_session(payload: RecipeSessionStartRequest, request: Request) -> RecipeSessionApiResponse:
    access_session = _require_demo_workflow_access(request, AiAccessWorkflow.RECIPE_SESSION)
    provider = _resolve_session_provider(payload)
    if payload.request_id:
        fingerprint = _start_request_fingerprint(payload)
        with default_recipe_start_idempotency_store.serialize(payload.request_id):
            interaction_id, conflict = default_recipe_start_idempotency_store.lookup(
                payload.request_id,
                fingerprint,
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Initial recipe request key was already used.")
            if interaction_id:
                existing = default_recipe_session_store.get_session(interaction_id)
                if existing is None:
                    default_recipe_start_idempotency_store.forget(payload.request_id)
                elif existing.draft is not None or existing.response_state in {
                    RecipeSessionResponseState.CLARIFICATION_NEEDED.value,
                    RecipeSessionResponseState.REJECTED.value,
                }:
                    log_ai_workflow(
                        "recipe.session.start",
                        request,
                        provider=existing.provider,
                        model=existing.model,
                        status="idempotent_replay",
                        retrieved_count=existing.retrieval.retrieved_count if existing.retrieval else 0,
                        citation_count=len(existing.citations),
                        warning_count=len(existing.warnings),
                    )
                    return _session_response(existing)
                else:
                    return _complete_recipe_session_start(
                        payload,
                        request,
                        access_session=access_session,
                        provider=provider,
                        existing_session=existing,
                    )
            return _complete_recipe_session_start(
                payload,
                request,
                access_session=access_session,
                provider=provider,
                request_fingerprint=fingerprint,
            )
    return _complete_recipe_session_start(
        payload,
        request,
        access_session=access_session,
        provider=provider,
    )


def _complete_recipe_session_start(
    payload: RecipeSessionStartRequest,
    request: Request,
    *,
    access_session,
    provider,
    existing_session: RecipeSessionState | None = None,
    request_fingerprint: str | None = None,
) -> RecipeSessionApiResponse:
    requirements = extract_recipe_requirements(payload.text)
    decision = decide_clarification(requirements)

    if requirements.confidence_label.value == "rejected":
        session = existing_session or default_recipe_session_store.create_session(requirements)
        _remember_start_request(payload, request_fingerprint, session)
        session = _update_session_metadata(
            session,
            response_state=RecipeSessionResponseState.REJECTED,
            warnings=["Input was rejected before retrieval or provider generation."],
        )
        log_ai_workflow("recipe.session.start", request, status="rejected", warning_count=1)
        return _session_response(session, decision=decision)

    if decision.should_clarify:
        requirements.open_questions = [
            RecipeClarificationQuestion(
                id="q1",
                question=decision.question or "What recipe detail should I use?",
                reason=decision.reason,
            )
        ]
        session = existing_session or default_recipe_session_store.create_session(requirements)
        _remember_start_request(payload, request_fingerprint, session)
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.CLARIFICATION_NEEDED)
        log_ai_workflow("recipe.session.start", request, status="clarification_needed", warning_count=0)
        return _session_response(session, decision=decision)

    session = existing_session or default_recipe_session_store.create_session(requirements)
    _remember_start_request(payload, request_fingerprint, session)
    session = _generate_and_store_draft(
        session,
        payload.text,
        response_state=RecipeSessionResponseState.DRAFT_GENERATED,
        source=payload.source,
        provider=provider,
        budget_session_state=access_session,
    )
    log_ai_workflow(
        "recipe.session.start",
        request,
        provider=session.provider,
        model=session.model,
        retrieved_count=session.retrieval.retrieved_count if session.retrieval else 0,
        citation_count=len(session.citations),
        warning_count=len(session.warnings),
    )
    return _session_response(session, decision=decision)


def _remember_start_request(
    payload: RecipeSessionStartRequest,
    request_fingerprint: str | None,
    session: RecipeSessionState,
) -> None:
    if payload.request_id and request_fingerprint:
        default_recipe_start_idempotency_store.remember(
            payload.request_id,
            request_fingerprint,
            session.interaction_id,
        )


def _start_request_fingerprint(payload: RecipeSessionStartRequest) -> str:
    encoded = json.dumps(
        {
            "text": payload.text,
            "source": payload.source,
            "provider_mode": payload.provider_mode,
            "model": payload.model,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@router.post("/{interaction_id}/message", response_model=RecipeSessionApiResponse)
def message_recipe_session(
    interaction_id: str,
    payload: RecipeSessionMessageRequest,
    request: Request,
) -> RecipeSessionApiResponse:
    access_session = _require_demo_workflow_access(request, AiAccessWorkflow.RECIPE_SESSION)
    session = _load_session_or_404(interaction_id)
    previous_requirements = session.requirements
    classification = classify_follow_up(payload.text, current_state=previous_requirements)
    current_servings = session.draft.servings if session.draft is not None else None
    serving_target = requested_serving_count(payload.text, current_servings)
    deterministic_serving_scale = is_serving_only_change(payload.text, current_servings)
    additive_serving_scale = is_additive_serving_change(payload.text, current_servings)

    if suggests_new_recipe(payload.text, previous_requirements):
        classification = RecipeFollowUpClassification(
            label=RecipeFollowUpLabel.NEW_RECIPE_SUGGESTED,
            reason="The message appears to request a different recipe.",
            clarification_may_be_needed=True,
        )
        decision = RecipeSessionDecision(
            should_clarify=True,
            question="That sounds like a different recipe. Do you want to start a new recipe and replace this draft?",
            reason="A new recipe requires explicit confirmation before replacing the current draft.",
            confidence_label=previous_requirements.confidence_label,
        )
        session = _update_session_metadata(
            session,
            response_state=RecipeSessionResponseState.NEW_RECIPE_CONFIRMATION,
        )
        return _session_response(
            session,
            classification=classification,
            decision=decision,
            previous_requirements=previous_requirements,
        )

    if session.revision_count >= MAX_RECIPE_CHANGES and classification.label != RecipeFollowUpLabel.IRRELEVANT_CHATTER:
        session = _update_session_metadata(
            session,
            response_state=RecipeSessionResponseState.CHANGE_LIMIT_REACHED,
        )
        return _session_response(session, classification=classification)

    if classification.label == RecipeFollowUpLabel.IRRELEVANT_CHATTER:
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.NO_MATERIAL_CHANGE)
        log_ai_workflow("recipe.session.message", request, status="no_material_change", warning_count=0)
        return _session_response(session, classification=classification, previous_requirements=previous_requirements)

    if classification.label == RecipeFollowUpLabel.SAVE_OR_FINALIZE_REQUEST:
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.READY_TO_FINALIZE)
        log_ai_workflow("recipe.session.message", request, status="ready_to_finalize", warning_count=0)
        return _session_response(session, classification=classification, previous_requirements=previous_requirements)

    if classification.label in {
        RecipeFollowUpLabel.REGENERATE_WITHOUT_NEW_REQUIREMENTS,
        RecipeFollowUpLabel.FORMATTING_ONLY,
    }:
        provider = _resolve_session_provider(payload)
        revised_requirements = previous_requirements.model_copy(deep=True)
        revised_requirements.latest_user_text = payload.text
        revised_requirements.revision_count += 1
        session = _generate_and_store_draft(
            session,
            _revision_generation_text(session.draft, payload.text),
            response_state=RecipeSessionResponseState.DRAFT_REVISED,
            budget_session_state=access_session,
            provider=provider,
            requirements_state=revised_requirements,
            previous_draft=session.draft,
            requested_change=payload.text,
            expected_servings=serving_target,
            deterministic_serving_scale=deterministic_serving_scale,
        )
        log_ai_workflow(
            "recipe.session.message",
            request,
            provider=session.provider,
            model=session.model,
            retrieved_count=session.retrieval.retrieved_count if session.retrieval else 0,
            citation_count=len(session.citations),
            warning_count=len(session.warnings),
        )
        return _session_response(
            session,
            classification=classification,
            rag_refreshed=False,
            previous_requirements=previous_requirements,
            provider_generation_occurred=True,
        )

    updated_requirements = _requirements_after_message(previous_requirements, payload.text, classification)
    refresh = decide_rag_refresh(previous_requirements, updated_requirements, follow_up=classification)
    clarification = decide_clarification(updated_requirements)
    if session.draft is not None and (
        classification.label == RecipeFollowUpLabel.RELEVANT_REQUIREMENT_UPDATE
        or serving_target is not None
    ):
        clarification = RecipeSessionDecision(
            should_clarify=False,
            reason="The existing draft supplies dish context for this relevant recipe change.",
            confidence_label=updated_requirements.confidence_label,
        )
    if clarification.should_clarify:
        updated_requirements.open_questions = [
            RecipeClarificationQuestion(
                id=f"q{len(updated_requirements.resolved_questions) + 1}",
                question=clarification.question or "What recipe detail should I use?",
                reason=clarification.reason,
            )
        ]
        session = default_recipe_session_store.update_session(
            interaction_id,
            updated_requirements,
            response_state=RecipeSessionResponseState.CLARIFICATION_NEEDED.value,
            warnings=session.warnings,
        )
        if session is None:
            raise _not_found()
        log_ai_workflow("recipe.session.message", request, status="clarification_needed", warning_count=0)
        return _session_response(
            session,
            classification=classification,
            decision=clarification,
            previous_requirements=previous_requirements,
        )

    response_state = (
        RecipeSessionResponseState.RAG_REFRESHED
        if refresh.should_refresh_rag
        else RecipeSessionResponseState.DRAFT_REVISED
    )
    session = _generate_and_store_draft(
        session,
        _revision_generation_text(session.draft, payload.text),
        response_state=response_state,
        budget_session_state=access_session,
        provider=_resolve_session_provider(payload),
        requirements_state=updated_requirements,
        previous_draft=session.draft,
        requested_change=payload.text,
        expected_servings=serving_target,
        deterministic_serving_scale=deterministic_serving_scale,
        additive_serving_scale=additive_serving_scale,
        required_additions=_new_required_ingredients(previous_requirements, updated_requirements),
    )
    log_ai_workflow(
        "recipe.session.message",
        request,
        provider=session.provider,
        model=session.model,
        status=response_state.value,
        retrieved_count=session.retrieval.retrieved_count if session.retrieval else 0,
        citation_count=len(session.citations),
        warning_count=len(session.warnings),
    )
    return _session_response(
        session,
        classification=classification,
        decision=clarification,
        rag_refreshed=refresh.should_refresh_rag,
        rag_refresh_reason=refresh.reason if refresh.should_refresh_rag else None,
        changed_fields=refresh.changed_fields,
        previous_requirements=previous_requirements,
        provider_generation_occurred=True,
    )


@router.get("/{interaction_id}", response_model=RecipeSessionApiResponse)
def get_recipe_session(interaction_id: str, request: Request) -> RecipeSessionApiResponse:
    # GET is part of the local recipe-session workflow and should respect the same gate.
    _require_demo_workflow_access(request, AiAccessWorkflow.RECIPE_SESSION)
    session = _load_session_or_404(interaction_id)
    return _session_response(session)


@router.post("/{interaction_id}/finalize", response_model=RecipeSessionApiResponse)
def finalize_recipe_session(
    interaction_id: str,
    payload: RecipeSessionFinalizeRequest,
    request: Request,
) -> RecipeSessionApiResponse:
    _require_demo_workflow_access(request, AiAccessWorkflow.RECIPE_SESSION)
    del payload
    session = _load_session_or_404(interaction_id)
    warnings = list(session.warnings)
    if session.draft is None:
        warnings.append("No generated draft is available to finalize.")
        session = _update_session_metadata(
            session,
            response_state=RecipeSessionResponseState.CLARIFICATION_NEEDED,
            warnings=warnings,
        )
        log_ai_workflow("recipe.session.finalize", request, status="clarification_needed", warning_count=len(warnings))
        return _session_response(session)

    finalize_warning = "Demo finalize only; no production cookbook write-back was performed."
    if finalize_warning not in warnings:
        warnings.append(finalize_warning)
    session = _update_session_metadata(
        session,
        response_state=RecipeSessionResponseState.READY_TO_FINALIZE,
        warnings=warnings,
        finalized_for_demo=True,
    )
    log_ai_workflow("recipe.session.finalize", request, status="ready_to_finalize", warning_count=len(warnings))
    return _session_response(session)


def _generate_and_store_draft(
    session: RecipeSessionState,
    text: str,
    *,
    response_state: RecipeSessionResponseState,
    source: str | None = None,
    budget_session_state: object | None = None,
    provider=None,
    requirements_state: RecipeRequirementsState | None = None,
    previous_draft: RecipeImportDraft | None = None,
    requested_change: str | None = None,
    expected_servings: int | None = None,
    deterministic_serving_scale: bool = False,
    additive_serving_scale: bool = False,
    required_additions: tuple[str, ...] = (),
) -> RecipeSessionState:
    try:
        response = import_recipe_text(RecipeImportRequest(text=text, source=source), provider=provider, session_state=budget_session_state or session)
    except RecipeImportProviderError as exc:
        raise HTTPException(status_code=503, detail=_safe_session_unavailable_detail(exc)) from exc
    except RecipeImportValidationError as exc:
        raise HTTPException(status_code=502, detail="Recipe-session provider returned an invalid draft.") from exc

    if response.draft is not None and previous_draft is not None and expected_servings is not None:
        if deterministic_serving_scale:
            response = response.model_copy(
                update={"draft": scale_recipe_draft(previous_draft, response.draft, expected_servings)},
                deep=True,
            )
        elif additive_serving_scale:
            if not all(draft_contains_ingredient(response.draft, item) for item in required_additions):
                raise HTTPException(
                    status_code=503,
                    detail={
                        "status": "unavailable",
                        "safe_unavailable_category": "ingredient_change_mismatch",
                        "safe_guidance": "Cookbook AI could not apply every requested ingredient change. Up to three bounded retries are allowed.",
                        "retryable": True,
                    },
                )
            response = response.model_copy(
                update={"draft": scale_additive_recipe_draft(previous_draft, response.draft, expected_servings)},
                deep=True,
            )
        elif response.draft.servings != expected_servings:
            log_ai_workflow(
                "recipe.session.serving_guard",
                provider=response.provider,
                model=response.model,
                status="rejected",
                safe_error_type="serving_scale_mismatch",
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unavailable",
                    "safe_unavailable_category": "serving_scale_mismatch",
                    "safe_guidance": "Cookbook AI could not scale this recipe consistently. Up to three bounded retries are allowed.",
                    "retryable": True,
                },
            )

    if previous_draft is not None and response.draft is not None and requested_change is not None:
        identity_check = validate_recipe_revision(previous_draft, response.draft, requested_change)
        if not identity_check.valid:
            log_ai_workflow(
                "recipe.session.revision_guard",
                provider=response.provider,
                model=response.model,
                status="rejected",
                safe_error_type="revision_identity_drift",
                safe_error_summary=",".join(identity_check.violation_codes),
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unavailable",
                    "safe_unavailable_category": "revision_identity_drift",
                    "safe_guidance": "Cookbook AI could not preserve this recipe. Up to three bounded retries are allowed.",
                    "retryable": True,
                },
            )

    # Provider generation must succeed before requirements/revision state is
    # committed. A failed request therefore leaves the current draft, context,
    # and ten-change allowance untouched.
    if response.draft is None and session.draft is not None:
        unchanged = default_recipe_session_store.update_session(
            session.interaction_id,
            session.requirements,
            response_state=RecipeSessionResponseState.REJECTED.value,
            draft=session.draft,
            citations=session.citations,
            retrieval=session.retrieval,
            warnings=response.warnings,
        )
        if unchanged is None:
            raise _not_found()
        return unchanged

    requirements = (requirements_state or session.requirements).model_copy(deep=True)
    requirements.last_support_level = response.retrieval.support_level if response.retrieval else None
    requirements.last_citation_ids = [citation.id for citation in response.citations]
    requirements.last_retrieval_cache_key = response.retrieval.cache.retrieval_cache_key if response.retrieval else None
    requirements.last_retrieval_summary = _requirements_retrieval_summary(response)

    response_state_value = response_state.value
    if response.draft is None:
        response_state_value = RecipeSessionResponseState.REJECTED.value

    updated = default_recipe_session_store.update_session(
        session.interaction_id,
        requirements,
        response_state=response_state_value,
        draft=response.draft,
        citations=response.citations,
        retrieval=response.retrieval,
        warnings=response.warnings,
        provider=response.provider,
        model=response.model,
    )
    if updated is None:
        raise _not_found()
    return updated


def _safe_session_unavailable_detail(exc: BaseException) -> dict[str, str | bool]:
    details = extract_provider_debug_details(exc)
    retryable_categories = {
        "timeout",
        "network",
        "provider_call_failed",
        "output_cap_or_incomplete_response",
        "invalid_json",
    }
    category = details.category if details else "unexpected_safe_internal_block"
    retryable = category in retryable_categories
    guidance = (
        "Cookbook AI could not complete this change. Up to three bounded retries are allowed."
        if retryable
        else "Cookbook AI could not complete this recipe change."
    )
    return {
        "status": "unavailable",
        "safe_unavailable_category": category,
        "safe_guidance": guidance,
        "retryable": retryable,
    }


def _requirements_after_message(
    previous: RecipeRequirementsState,
    message: str,
    classification: RecipeFollowUpClassification,
) -> RecipeRequirementsState:
    combined_text = f"{previous.latest_user_text.strip()} {message.strip()}".strip()
    updated = extract_recipe_requirements(
        combined_text,
        interaction_id=previous.interaction_id,
        now=datetime.now(UTC),
    )
    updated.original_user_text = previous.original_user_text
    previous_servings = int(previous.serving_count.value) if previous.serving_count else None
    serving_target = requested_serving_count(message, previous_servings)
    if serving_target is not None:
        updated.serving_count = RecipeRequirementField(
            value=serving_target,
            source=RecipeRequirementSource.USER_PROVIDED,
        )
    # Answering an open question completes the pending request; it is not an
    # additional recipe change. This also keeps pre-draft clarification at
    # revision zero so users still receive all ten post-draft changes.
    updated.revision_count = previous.revision_count + (
        0 if classification.label == RecipeFollowUpLabel.CLARIFICATION_ANSWER else 1
    )
    updated.last_retrieval_summary = previous.last_retrieval_summary
    updated.last_retrieval_cache_key = previous.last_retrieval_cache_key
    updated.last_support_level = previous.last_support_level
    updated.last_citation_ids = list(previous.last_citation_ids)
    if classification.label == RecipeFollowUpLabel.CLARIFICATION_ANSWER:
        for question in previous.open_questions:
            updated.resolved_questions.append(
                RecipeResolvedQuestion(
                    question=question.question,
                    answer=message.strip(),
                    resolved_at=datetime.now(UTC),
                )
            )
        updated.open_questions = []
        _mark_latest_user_values_as_clarified(updated)
    return updated


def _new_required_ingredients(
    previous: RecipeRequirementsState,
    updated: RecipeRequirementsState,
) -> tuple[str, ...]:
    existing = {str(item.value) for item in previous.required_ingredients}
    return tuple(str(item.value) for item in updated.required_ingredients if str(item.value) not in existing)


def _mark_latest_user_values_as_clarified(state: RecipeRequirementsState) -> None:
    if state.dish_intent:
        state.dish_intent.source = RecipeRequirementSource.CLARIFIED_BY_USER
    if state.cooking_method:
        state.cooking_method.source = RecipeRequirementSource.CLARIFIED_BY_USER


def _revision_generation_text(draft, message: str) -> str:
    if draft is None:
        return message.strip()
    ingredients = "; ".join(
        " ".join(str(value) for value in (item.quantity, item.unit, item.name, item.note) if value)
        for item in draft.ingredients
    )
    instructions = "; ".join(item.text for item in draft.instructions)
    return (
        "Revise the current recipe only and return one complete, internally coherent recipe. "
        "LOCKED INVARIANTS: preserve the dish identity, base starch, protein, cooking method, and all existing "
        "ingredients and instruction actions unless the requested change explicitly replaces or removes them. "
        "Change only fields required by the requested change. Every instruction must still describe the current "
        "dish and must use its established base ingredients. Never introduce a different staple, dish type, soup, "
        "or cooking method merely because a retrieved example contains one. Check the final ingredients against "
        "the final instructions before responding. "
        "For a serving change, use the exact requested serving count and scale every numeric ingredient quantity "
        "by the same new-servings/current-servings ratio. Do not scale temperatures or cooking times linearly. "
        f"Requested change: {message.strip()}. "
        f"Current title: {draft.title}. "
        f"Description: {draft.description or ''}. Servings: {draft.servings or 4}. "
        f"Ingredients: {ingredients}. Instructions: {instructions}."
    )[:8000]


def _update_session_metadata(
    session: RecipeSessionState,
    *,
    response_state: RecipeSessionResponseState,
    warnings: list[str] | None = None,
    finalized_for_demo: bool | None = None,
) -> RecipeSessionState:
    updated = default_recipe_session_store.update_session(
        session.interaction_id,
        session.requirements,
        response_state=response_state.value,
        draft=session.draft,
        citations=session.citations,
        retrieval=session.retrieval,
        warnings=warnings if warnings is not None else session.warnings,
        finalized_for_demo=finalized_for_demo,
    )
    if updated is None:
        raise _not_found()
    return updated


def _session_response(
    session: RecipeSessionState,
    *,
    decision: RecipeSessionDecision | None = None,
    classification: RecipeFollowUpClassification | None = None,
    rag_refreshed: bool = False,
    rag_refresh_reason: str | None = None,
    changed_fields: list[str] | None = None,
    previous_requirements: RecipeRequirementsState | None = None,
    provider_generation_occurred: bool = False,
) -> RecipeSessionApiResponse:
    state = session.response_state or RecipeSessionResponseState.NO_MATERIAL_CHANGE.value
    clarification_question = None
    if session.requirements.open_questions:
        clarification_question = session.requirements.open_questions[0].question
    elif decision and decision.question:
        clarification_question = decision.question
    diff = None
    revision_summary = None
    if previous_requirements is not None:
        diff = build_requirement_diff(
            previous_requirements,
            session.requirements,
            rag_refresh_relevant=rag_refreshed,
            rag_refresh_reason=rag_refresh_reason,
        )
        revision_summary = build_revision_summary(
            diff,
            response_state=state,
            rag_refreshed=rag_refreshed,
            provider_generation_occurred=provider_generation_occurred,
        )
    return RecipeSessionApiResponse(
        interaction_id=session.interaction_id,
        response_state=state,
        requirements=_requirements_response(session.requirements),
        decision=_decision_response(decision=decision, classification=classification),
        clarification_question=clarification_question,
        rag_refreshed=rag_refreshed,
        rag_refresh_reason=rag_refresh_reason,
        changed_fields=changed_fields if changed_fields is not None else (diff.changed_fields if diff else []),
        requirement_diff=RecipeSessionRequirementDiffResponse(**diff.model_dump()) if diff else None,
        revision_summary=revision_summary,
        draft=session.draft.model_dump() if session.draft else None,
        draft_summary=_draft_summary(session.draft),
        citations=[citation.model_dump() for citation in session.citations],
        retrieval=session.retrieval.model_dump() if session.retrieval else None,
        retrieval_summary=_retrieval_summary_response(session),
        support_level=session.retrieval.support_level if session.retrieval else session.requirements.last_support_level,
        provider=session.provider,
        model=session.model,
        revision_count=session.revision_count,
        expires_at=session.expires_at.isoformat(),
        warnings=session.warnings,
    )


def _requirements_response(state: RecipeRequirementsState) -> RecipeSessionRequirementsResponse:
    return RecipeSessionRequirementsResponse(
        dish_intent=_field_response(state.dish_intent),
        serving_count=_field_response(state.serving_count),
        required_ingredients=_field_list_response(state.required_ingredients),
        optional_ingredients=_field_list_response(state.optional_ingredients),
        excluded_ingredients=_field_list_response(state.excluded_ingredients),
        cooking_method=_field_response(state.cooking_method),
        equipment_constraints=_field_list_response(state.equipment_constraints),
        time_constraints=_field_list_response(state.time_constraints),
        dietary_constraints=_field_list_response(state.dietary_constraints),
        texture_or_style_goals=_field_list_response(state.texture_or_style_goals),
        assumptions=_field_list_response(state.assumptions),
        requirement_sources=state.requirement_sources,
        confidence_label=state.confidence_label.value,
        open_questions=[question.question for question in state.open_questions],
        resolved_questions=[
            {
                "question": question.question,
                "answer": question.answer,
                "resolved_at": question.resolved_at.isoformat(),
            }
            for question in state.resolved_questions
        ],
    )


def _decision_response(
    *,
    decision: RecipeSessionDecision | None = None,
    classification: RecipeFollowUpClassification | None = None,
) -> RecipeSessionDecisionResponse | None:
    if decision is None and classification is None:
        return None
    return RecipeSessionDecisionResponse(
        should_clarify=decision.should_clarify if decision else None,
        question=decision.question if decision else None,
        reason=classification.reason if classification else (decision.reason if decision else None),
        confidence_label=decision.confidence_label.value if decision else None,
        delta_label=classification.label.value if classification else None,
        provider_generation_likely_needed=classification.provider_generation_likely_needed if classification else None,
        clarification_may_be_needed=classification.clarification_may_be_needed if classification else None,
    )


def _field_response(field: RecipeRequirementField | None) -> RecipeRequirementValueResponse | None:
    if field is None:
        return None
    return RecipeRequirementValueResponse(value=field.value, source=field.source.value)


def _field_list_response(fields: list[RecipeRequirementField]) -> list[RecipeRequirementValueResponse]:
    return [_field_response(field) for field in fields if _field_response(field) is not None]


def _draft_summary(draft) -> RecipeSessionDraftSummary | None:
    if draft is None:
        return None
    return RecipeSessionDraftSummary(
        title=draft.title,
        servings=draft.servings,
        ingredient_count=len(draft.ingredients),
        instruction_count=len(draft.instructions),
    )


def _requirements_retrieval_summary(response) -> RecipeRetrievalSummary | None:
    if response.retrieval is None:
        return None
    return RecipeRetrievalSummary(
        query=response.retrieval.query,
        retrieved_count=response.retrieval.retrieved_count,
        top_titles=[citation.title for citation in response.citations[:3]],
        relevance_category=response.retrieval.relevance_category,
    )


def _retrieval_summary_response(session: RecipeSessionState) -> RecipeSessionRetrievalSummary | None:
    summary = session.requirements.last_retrieval_summary
    if summary is None:
        return None
    return RecipeSessionRetrievalSummary(
        query=summary.query,
        retrieved_count=summary.retrieved_count,
        top_titles=summary.top_titles,
        relevance_category=summary.relevance_category,
        rag_refresh_reason=summary.rag_refresh_reason,
    )


def _load_session_or_404(interaction_id: str) -> RecipeSessionState:
    session = default_recipe_session_store.get_session(interaction_id)
    if session is None:
        raise _not_found()
    return session


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"response_state": RecipeSessionResponseState.NOT_FOUND.value, "message": "Recipe session was not found or has expired."})


def _require_demo_workflow_access(request: Request, workflow: AiAccessWorkflow):
    return require_demo_workflow_access(
        workflow,
        request.headers,
        client_host=request.client.host if request.client else None,
    )
