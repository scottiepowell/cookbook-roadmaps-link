"""Public-fixture-only advisory tasks; no recipe or account persistence."""

from __future__ import annotations

import os
import re
import time
from threading import Lock

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.ai_access_models import AiAccessWorkflow
from app.ai_budget_guard import check_provider_budget
from app.ai_invite_sessions import require_demo_workflow_access
from app.observability import log_ai_stage, log_event
from app.providers.groq_offload import GroqOffloadProvider


TASKS = {
    "recipe_titles": "Suggest concise recipe titles from each supplied public dish idea.",
    "ingredient_parse": "Suggest a normalized ingredient name and unit for each supplied line; preserve its quantity.",
    "instruction_cleanup": "Suggest clearer wording for each instruction without changing ingredients or cooking meaning.",
    "substitution_ideas": "Suggest optional non-allergy substitutions for each ingredient; do not claim equivalence.",
    "shopping_group": "Suggest an ordinary grocery aisle label for each supplied item; add no purchases.",
    "pantry_ideas": "Suggest one meal idea using each supplied shelf-stable ingredient; do not assess freshness.",
    "meal_ideas": "Suggest a short meal idea for each supplied public recipe title or ingredient set.",
    "plain_language": "Rewrite each supplied line in plain language, preserving quantities and names.",
    "query_expansion": "Suggest one short search synonym for each supplied public ingredient or dish term.",
}


class AdvisoryRequest(BaseModel):
    task: str
    text: str = Field(min_length=1, max_length=1500)
    public_or_synthetic: bool = False


class AdvisoryItem(BaseModel):
    source: str
    suggestion: str


class AdvisoryResponse(BaseModel):
    status: str
    task: str
    items: list[AdvisoryItem]
    provider: str
    usage: dict[str, int] | None = None


router = APIRouter(prefix="/ai/advisory", tags=["advisory"])
_provider: GroqOffloadProvider | None = None
_provider_lock = Lock()
_SAFE_TEXT = re.compile(r"\b(?:allerg(?:y|ic|en)|medical|medicine|diagnos(?:e|is)|prescription)\b|@|https?://", re.I)


def _active_provider() -> GroqOffloadProvider:
    global _provider
    with _provider_lock:
        if _provider is None:
            _provider = GroqOffloadProvider()
        return _provider


@router.post("", response_model=AdvisoryResponse)
def advise(payload: AdvisoryRequest, request: Request) -> AdvisoryResponse:
    require_demo_workflow_access(
        AiAccessWorkflow.RECIPE_SESSION,
        request.headers,
        client_host=request.client.host if request.client else None,
    )
    if not payload.public_or_synthetic:
        raise HTTPException(400, "Confirm that this input is public or invented.")
    if payload.task not in TASKS:
        raise HTTPException(400, "Unknown advisory task.")
    enabled = os.getenv("AI_OFFLOAD_ENABLED", "false").lower() in {"1", "true", "yes"}
    allowed = {part.strip() for part in os.getenv("AI_OFFLOAD_ALLOWED_TASKS", "").split(",")}
    if not enabled or payload.task not in allowed:
        raise HTTPException(503, "This advisory task is unavailable.")
    sources = [part.strip() for part in payload.text.splitlines() if part.strip()]
    if not sources or len(sources) > 12 or any(len(part) > 120 for part in sources):
        raise HTTPException(400, "Enter up to 12 short lines.")
    if _SAFE_TEXT.search(payload.text):
        raise HTTPException(400, "This pilot accepts only public, non-sensitive cooking text.")
    lines = [{"source_id": f"s{index}", "text": source} for index, source in enumerate(sources)]
    try:
        provider = _active_provider()
    except Exception:
        raise HTTPException(503, "This advisory task is unavailable.") from None
    budget = check_provider_budget(
        AiAccessWorkflow.RECIPE_SESSION, provider.name, provider.model,
        (len(payload.text) + 300) // 4, 500, None,
    )
    if not budget.allowed:
        raise HTTPException(429, "Advisory call limit reached.")
    started = time.perf_counter()
    try:
        items, usage = provider.generate(task=TASKS[payload.task], task_key=payload.task, lines=lines)
    except Exception:
        log_ai_stage("groq.advisory", duration_ms=(time.perf_counter() - started) * 1000,
                     status="fallback", provider="groq", model=provider.model)
        log_event("ai.offload", task=payload.task, provider="groq", status="fallback")
        return AdvisoryResponse(
            status="fallback", task=payload.task, provider="none",
            items=[AdvisoryItem(source=source, suggestion=source) for source in sources],
        )
    log_ai_stage("groq.advisory", duration_ms=(time.perf_counter() - started) * 1000,
                 status="ok", provider="groq", model=provider.model)
    log_event("ai.offload", task=payload.task, provider="groq", status="ok",
              input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"])
    return AdvisoryResponse(
        status="ok", task=payload.task, provider="groq", usage=usage,
        items=[AdvisoryItem(source=source, suggestion=item["suggestion"])
               for source, item in zip(sources, items, strict=True)],
    )
