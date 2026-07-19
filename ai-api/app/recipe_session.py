from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import BaseModel, Field

from app.recipe_requirements import RecipeRequirementsState
from app.schemas import RecipeImportCitation, RecipeImportDraft, RecipeImportRetrievalMetadata


class RecipeSessionState(BaseModel):
    interaction_id: str
    requirements: RecipeRequirementsState
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    revision_count: int = 0
    response_state: str | None = None
    draft: RecipeImportDraft | None = None
    citations: list[RecipeImportCitation] = Field(default_factory=list)
    retrieval: RecipeImportRetrievalMetadata | None = None
    warnings: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    finalized_for_demo: bool = False


class RecipeRequirementDiffSummary(BaseModel):
    """Safe, deterministic operator summary of a requirements revision."""

    changed_fields: list[str] = Field(default_factory=list)
    added_requirements: dict[str, list[str]] = Field(default_factory=dict)
    removed_requirements: dict[str, list[str]] = Field(default_factory=dict)
    updated_requirements: dict[str, str] = Field(default_factory=dict)
    summary_message: str
    rag_refresh_relevant: bool = False
    rag_refresh_reason: str | None = None
    previous_revision: int = 0
    current_revision: int = 0


_DIFF_FIELDS = (
    "dish_intent",
    "serving_count",
    "required_ingredients",
    "optional_ingredients",
    "excluded_ingredients",
    "cooking_method",
    "equipment_constraints",
    "time_constraints",
    "dietary_constraints",
    "texture_or_style_goals",
    "assumptions",
    "open_questions",
    "resolved_questions",
)
_RETRIEVAL_RELEVANT_FIELDS = {
    "dish_intent",
    "required_ingredients",
    "excluded_ingredients",
    "cooking_method",
    "equipment_constraints",
    "time_constraints",
    "dietary_constraints",
}


def build_requirement_diff(
    previous: RecipeRequirementsState,
    current: RecipeRequirementsState,
    *,
    rag_refresh_relevant: bool = False,
    rag_refresh_reason: str | None = None,
) -> RecipeRequirementDiffSummary:
    """Compare safe requirement values without retaining or exposing message text."""

    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    updated: dict[str, str] = {}
    changed: list[str] = []
    for field_name in _DIFF_FIELDS:
        before = _diff_values(previous, field_name)
        after = _diff_values(current, field_name)
        if before == after:
            continue
        changed.append(field_name)
        if len(before) == 1 and len(after) == 1:
            updated[field_name] = f"{before[0]} -> {after[0]}"
            continue
        field_added = [value for value in after if value not in before]
        field_removed = [value for value in before if value not in after]
        if field_added:
            added[field_name] = field_added[:6]
        if field_removed:
            removed[field_name] = field_removed[:6]

    relevant = rag_refresh_relevant or any(field in _RETRIEVAL_RELEVANT_FIELDS for field in changed)
    if not changed:
        message = "No material recipe requirements changed; existing draft and citations were reused."
    elif relevant:
        message = f"Updated {', '.join(changed[:3])}; RAG refreshed because the change affects retrieval."
    else:
        message = f"Updated {', '.join(changed[:3])}; existing retrieval was reused."
    return RecipeRequirementDiffSummary(
        changed_fields=changed,
        added_requirements=added,
        removed_requirements=removed,
        updated_requirements=updated,
        summary_message=message,
        rag_refresh_relevant=relevant,
        rag_refresh_reason=rag_refresh_reason,
        previous_revision=previous.revision_count,
        current_revision=current.revision_count,
    )


def build_revision_summary(
    diff: RecipeRequirementDiffSummary,
    *,
    response_state: str,
    rag_refreshed: bool,
    provider_generation_occurred: bool,
) -> str:
    """Return one concise operator-facing sentence from safe structured metadata."""

    revision = diff.current_revision
    if not diff.changed_fields:
        action = "existing draft and citations were reused"
        if not provider_generation_occurred:
            action += "; no new provider generation occurred"
        return f"Revision {revision}: No material requirements changed; {action}."
    change = ", ".join(diff.changed_fields[:2])
    if rag_refreshed:
        return f"Revision {revision}: Changed {change}; RAG refreshed because the change affects retrieval."
    return f"Revision {revision}: Changed {change}; existing retrieval was reused."


def _diff_values(state: RecipeRequirementsState, field_name: str) -> list[str]:
    value = getattr(state, field_name)
    if value is None:
        return []
    if field_name == "resolved_questions":
        return ["resolved question"] * len(value)
    if field_name == "open_questions":
        return ["open question"] * len(value)
    if isinstance(value, list):
        return [str(item.value) for item in value]
    return [str(value.value)]


class RecipeSessionStore:
    """Small process-local store for alpha tests and local demos only."""

    def __init__(self, *, max_sessions: int = 32, ttl_seconds: int = 3600) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be at least 1")
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self._sessions: OrderedDict[str, RecipeSessionState] = OrderedDict()

    def create_session(
        self,
        requirements_state: RecipeRequirementsState,
        *,
        now: datetime | None = None,
        interaction_id: str | None = None,
    ) -> RecipeSessionState:
        current_time = now or datetime.now(UTC)
        session_id = interaction_id or requirements_state.interaction_id or f"rs_{uuid4().hex[:12]}"
        expires_at = current_time + timedelta(seconds=self.ttl_seconds)
        updated_requirements = requirements_state.model_copy(
            update={
                "interaction_id": session_id,
                "updated_at": current_time,
                "expires_at": expires_at,
            },
            deep=True,
        )
        if updated_requirements.created_at > current_time:
            updated_requirements.created_at = current_time
        session = RecipeSessionState(
            interaction_id=session_id,
            requirements=updated_requirements,
            created_at=updated_requirements.created_at,
            updated_at=current_time,
            expires_at=expires_at,
            revision_count=updated_requirements.revision_count,
        )
        self.expire_sessions(current_time)
        self._sessions[session_id] = session
        self._sessions.move_to_end(session_id)
        self._evict_over_limit()
        return session

    def get_session(self, interaction_id: str, *, now: datetime | None = None) -> RecipeSessionState | None:
        current_time = now or datetime.now(UTC)
        self.expire_sessions(current_time)
        session = self._sessions.get(interaction_id)
        if session is None:
            return None
        self._sessions.move_to_end(interaction_id)
        return session

    def update_session(
        self,
        interaction_id: str,
        updated_state: RecipeRequirementsState,
        *,
        now: datetime | None = None,
        response_state: str | None = None,
        draft: RecipeImportDraft | None = None,
        citations: list[RecipeImportCitation] | None = None,
        retrieval: RecipeImportRetrievalMetadata | None = None,
        warnings: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        finalized_for_demo: bool | None = None,
    ) -> RecipeSessionState | None:
        current_time = now or datetime.now(UTC)
        existing = self.get_session(interaction_id, now=current_time)
        if existing is None:
            return None
        expires_at = current_time + timedelta(seconds=self.ttl_seconds)
        requirements = updated_state.model_copy(
            update={
                "interaction_id": interaction_id,
                "updated_at": current_time,
                "expires_at": expires_at,
                "revision_count": updated_state.revision_count,
            },
            deep=True,
        )
        session = RecipeSessionState(
            interaction_id=interaction_id,
            requirements=requirements,
            created_at=existing.created_at,
            updated_at=current_time,
            expires_at=expires_at,
            revision_count=requirements.revision_count,
            response_state=response_state if response_state is not None else existing.response_state,
            draft=draft if draft is not None else existing.draft,
            citations=citations if citations is not None else existing.citations,
            retrieval=retrieval if retrieval is not None else existing.retrieval,
            warnings=warnings if warnings is not None else existing.warnings,
            provider=provider if provider is not None else existing.provider,
            model=model if model is not None else existing.model,
            finalized_for_demo=finalized_for_demo if finalized_for_demo is not None else existing.finalized_for_demo,
        )
        self._sessions[interaction_id] = session
        self._sessions.move_to_end(interaction_id)
        return session

    def expire_sessions(self, now: datetime | None = None) -> int:
        current_time = now or datetime.now(UTC)
        expired_ids = [
            interaction_id
            for interaction_id, session in self._sessions.items()
            if session.expires_at <= current_time
        ]
        for interaction_id in expired_ids:
            self._sessions.pop(interaction_id, None)
        return len(expired_ids)

    def clear(self) -> None:
        self._sessions.clear()

    def count(self, *, now: datetime | None = None) -> int:
        self.expire_sessions(now)
        return len(self._sessions)

    def list_session_ids(self, *, now: datetime | None = None) -> list[str]:
        self.expire_sessions(now)
        return list(self._sessions.keys())

    def _evict_over_limit(self) -> None:
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)


default_recipe_session_store = RecipeSessionStore()
