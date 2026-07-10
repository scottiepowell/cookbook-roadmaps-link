from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request

from app.importer import RecipeImportProviderError, RecipeImportValidationError, import_recipe_text
from app.observability import log_ai_workflow
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
)
from app.recipe_session import RecipeSessionState, default_recipe_session_store
from app.schemas import (
    RecipeImportRequest,
    RecipeRequirementValueResponse,
    RecipeSessionApiResponse,
    RecipeSessionDecisionResponse,
    RecipeSessionDraftSummary,
    RecipeSessionFinalizeRequest,
    RecipeSessionMessageRequest,
    RecipeSessionRequirementsResponse,
    RecipeSessionRetrievalSummary,
    RecipeSessionStartRequest,
)


router = APIRouter(prefix="/ai/recipe-session", tags=["recipe-session-alpha"])


@router.post("/start", response_model=RecipeSessionApiResponse)
def start_recipe_session(payload: RecipeSessionStartRequest, request: Request) -> RecipeSessionApiResponse:
    requirements = extract_recipe_requirements(payload.text)
    decision = decide_clarification(requirements)

    if requirements.confidence_label.value == "rejected":
        session = default_recipe_session_store.create_session(requirements)
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
        session = default_recipe_session_store.create_session(requirements)
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.CLARIFICATION_NEEDED)
        log_ai_workflow("recipe.session.start", request, status="clarification_needed", warning_count=0)
        return _session_response(session, decision=decision)

    session = default_recipe_session_store.create_session(requirements)
    session = _generate_and_store_draft(
        session,
        _generation_text(requirements),
        response_state=RecipeSessionResponseState.DRAFT_GENERATED,
        source=payload.source,
    )
    log_ai_workflow(
        "recipe.session.start",
        request,
        provider="mock" if session.draft else None,
        model=None,
        retrieved_count=session.retrieval.retrieved_count if session.retrieval else 0,
        citation_count=len(session.citations),
        warning_count=len(session.warnings),
    )
    return _session_response(session, decision=decision)


@router.post("/{interaction_id}/message", response_model=RecipeSessionApiResponse)
def message_recipe_session(
    interaction_id: str,
    payload: RecipeSessionMessageRequest,
    request: Request,
) -> RecipeSessionApiResponse:
    session = _load_session_or_404(interaction_id)
    previous_requirements = session.requirements
    classification = classify_follow_up(payload.text, current_state=previous_requirements)

    if classification.label in {
        RecipeFollowUpLabel.IRRELEVANT_CHATTER,
        RecipeFollowUpLabel.FORMATTING_ONLY,
    }:
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.NO_MATERIAL_CHANGE)
        log_ai_workflow("recipe.session.message", request, status="no_material_change", warning_count=0)
        return _session_response(session, classification=classification)

    if classification.label == RecipeFollowUpLabel.SAVE_OR_FINALIZE_REQUEST:
        session = _update_session_metadata(session, response_state=RecipeSessionResponseState.READY_TO_FINALIZE)
        log_ai_workflow("recipe.session.message", request, status="ready_to_finalize", warning_count=0)
        return _session_response(session, classification=classification)

    if classification.label == RecipeFollowUpLabel.REGENERATE_WITHOUT_NEW_REQUIREMENTS:
        session = _generate_and_store_draft(
            session,
            _generation_text(previous_requirements),
            response_state=RecipeSessionResponseState.DRAFT_REVISED,
        )
        log_ai_workflow(
            "recipe.session.message",
            request,
            retrieved_count=session.retrieval.retrieved_count if session.retrieval else 0,
            citation_count=len(session.citations),
            warning_count=len(session.warnings),
        )
        return _session_response(session, classification=classification, rag_refreshed=False)

    updated_requirements = _requirements_after_message(previous_requirements, payload.text, classification)
    refresh = decide_rag_refresh(previous_requirements, updated_requirements, follow_up=classification)
    clarification = decide_clarification(updated_requirements)
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
        return _session_response(session, classification=classification, decision=clarification)

    response_state = (
        RecipeSessionResponseState.RAG_REFRESHED
        if refresh.should_refresh_rag
        else RecipeSessionResponseState.DRAFT_REVISED
    )
    session = default_recipe_session_store.update_session(
        interaction_id,
        updated_requirements,
        response_state=response_state.value,
        warnings=session.warnings,
    )
    if session is None:
        raise _not_found()
    session = _generate_and_store_draft(
        session,
        _generation_text(updated_requirements),
        response_state=response_state,
    )
    log_ai_workflow(
        "recipe.session.message",
        request,
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
    )


@router.get("/{interaction_id}", response_model=RecipeSessionApiResponse)
def get_recipe_session(interaction_id: str) -> RecipeSessionApiResponse:
    session = _load_session_or_404(interaction_id)
    return _session_response(session)


@router.post("/{interaction_id}/finalize", response_model=RecipeSessionApiResponse)
def finalize_recipe_session(
    interaction_id: str,
    payload: RecipeSessionFinalizeRequest,
    request: Request,
) -> RecipeSessionApiResponse:
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
) -> RecipeSessionState:
    try:
        response = import_recipe_text(RecipeImportRequest(text=text, source=source))
    except RecipeImportProviderError as exc:
        raise HTTPException(status_code=503, detail="Recipe-session provider is not available.") from exc
    except RecipeImportValidationError as exc:
        raise HTTPException(status_code=502, detail="Recipe-session provider returned an invalid draft.") from exc

    requirements = session.requirements.model_copy(deep=True)
    requirements.last_support_level = response.retrieval.support_level if response.retrieval else None
    requirements.last_citation_ids = [citation.id for citation in response.citations]
    requirements.last_retrieval_cache_key = response.retrieval.cache.retrieval_cache_key if response.retrieval else None
    requirements.last_retrieval_summary = _requirements_retrieval_summary(response)

    updated = default_recipe_session_store.update_session(
        session.interaction_id,
        requirements,
        response_state=response_state.value,
        draft=response.draft,
        citations=response.citations,
        retrieval=response.retrieval,
        warnings=response.warnings,
    )
    if updated is None:
        raise _not_found()
    return updated


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
    updated.revision_count = previous.revision_count + 1
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


def _mark_latest_user_values_as_clarified(state: RecipeRequirementsState) -> None:
    if state.dish_intent:
        state.dish_intent.source = RecipeRequirementSource.CLARIFIED_BY_USER
    if state.cooking_method:
        state.cooking_method.source = RecipeRequirementSource.CLARIFIED_BY_USER


def _generation_text(requirements: RecipeRequirementsState) -> str:
    parts = []
    if requirements.dish_intent:
        parts.append(str(requirements.dish_intent.value))
    parts.append("recipe")
    if requirements.serving_count:
        parts.append(f"for {requirements.serving_count.value} servings")
    if requirements.required_ingredients:
        parts.append("with " + " ".join(str(field.value) for field in requirements.required_ingredients))
    if requirements.excluded_ingredients:
        parts.append("without " + " ".join(str(field.value) for field in requirements.excluded_ingredients))
    if requirements.cooking_method:
        parts.append(str(requirements.cooking_method.value))
    if requirements.equipment_constraints:
        parts.append("equipment " + " ".join(str(field.value) for field in requirements.equipment_constraints))
    if requirements.dietary_constraints:
        parts.append(" ".join(str(field.value) for field in requirements.dietary_constraints))
    if requirements.time_constraints:
        parts.append(" ".join(str(field.value) for field in requirements.time_constraints))
    if len(parts) <= 3:
        parts.append(requirements.latest_user_text)
    text = " ".join(part for part in parts if part).strip()
    if len(text) <= 190:
        return text
    return text[:190].rsplit(" ", 1)[0].strip()


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
) -> RecipeSessionApiResponse:
    state = session.response_state or RecipeSessionResponseState.NO_MATERIAL_CHANGE.value
    clarification_question = None
    if session.requirements.open_questions:
        clarification_question = session.requirements.open_questions[0].question
    elif decision and decision.question:
        clarification_question = decision.question
    return RecipeSessionApiResponse(
        interaction_id=session.interaction_id,
        response_state=state,
        requirements=_requirements_response(session.requirements),
        decision=_decision_response(decision=decision, classification=classification),
        clarification_question=clarification_question,
        rag_refreshed=rag_refreshed,
        rag_refresh_reason=rag_refresh_reason,
        changed_fields=changed_fields or [],
        draft=session.draft.model_dump() if session.draft else None,
        draft_summary=_draft_summary(session.draft),
        citations=[citation.model_dump() for citation in session.citations],
        retrieval=session.retrieval.model_dump() if session.retrieval else None,
        retrieval_summary=_retrieval_summary_response(session),
        support_level=session.retrieval.support_level if session.retrieval else session.requirements.last_support_level,
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
