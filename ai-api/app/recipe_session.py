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
    finalized_for_demo: bool = False


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
