"""Optional lossless public-dataset context deduplication before final generation.

No user query, saved recipe, or conversation is sent to Groq. The operator must
pin all approved dataset bytes; replacing any source fails closed.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import BoundedSemaphore, Lock
import time

from app.ai_access_models import AiAccessWorkflow
from app.ai_budget_guard import check_provider_budget
from app.config import get_recipe_dataset_dir
from app.observability import log_event
from app.providers.groq_offload import GroqOffloadProvider

_slots = BoundedSemaphore(2)
_lock = Lock()
_provider = None
_fingerprint = None


def _enabled(name):
    return os.getenv(name, "false").lower() in {"true", "1", "yes"}


def _approved_dataset():
    global _fingerprint
    expected = os.getenv("AI_RAG_PUBLIC_DATASET_SHA256", "")
    if len(expected) != 64:
        return False
    root = Path(get_recipe_dataset_dir())
    try:
        paths = [root / name for name in ("13k-recipes.csv", "13k-recipes.db", "5k-recipes.db")]
        key = tuple((str(path.resolve()), path.stat().st_mtime_ns, path.stat().st_size)
                    if path.exists() else (str(path.resolve()), None, None) for path in paths)
        with _lock:
            if _fingerprint is None or _fingerprint[0] != key:
                digest = sha256()
                for path in paths:
                    digest.update(path.name.encode())
                    digest.update(sha256(path.read_bytes()).digest() if path.exists() else b"missing")
                _fingerprint = (key, digest.hexdigest())
            return _fingerprint[1] == expected
    except OSError:
        return False


def redundant_snippet(item):
    """Exact substring evidence only; token overlap could lose negation/meaning."""
    snippet = " ".join(item.snippet.split()).strip()
    evidence = [item.title, item.instruction_summary, *item.key_ingredients,
                ", ".join(item.key_ingredients)]
    return bool(snippet) and any(snippet in " ".join(text.split()) for text in evidence)


def optimize_context(pack, session_state=None):
    """Return original pack on every ineligible, invalid, or failed offload."""
    global _provider
    groq = _enabled("AI_RAG_GROQ_DEDUP_ENABLED") and _enabled("AI_OFFLOAD_ENABLED")
    local = _enabled("AI_RAG_DEDUP_ENABLED")
    if pack is None or not pack.items or not (groq or local):
        return pack
    eligible = {f"s{i}" for i, item in enumerate(pack.items) if redundant_snippet(item)}
    if not eligible:
        return pack
    if not groq:
        return _without_snippets(pack, eligible)
    if not _approved_dataset() or not _slots.acquire(blocking=False):
        return pack
    started = time.perf_counter()
    usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0, "responses": 0}
    status = "fallback"
    result = pack
    try:
        with _lock:
            if _provider is None:
                _provider = GroqOffloadProvider()
        # Send only duplicated public excerpts, never pack.query or user state.
        lines = [{"source_id": f"s{i}", "text": json.dumps({
            "snippet": item.snippet, "title": item.title,
            "ingredients": item.key_ingredients, "instructions": item.instruction_summary,
        })} for i, item in enumerate(pack.items)]
        if len(json.dumps(lines)) > 6000:
            return pack

        def reserve():
            decision = check_provider_budget(AiAccessWorkflow.IMPORTER, "groq", _provider.model,
                                             len(json.dumps(lines)) + 300, 500, session_state)
            if not decision.allowed:
                raise RuntimeError("budget")
            usage["attempts"] += 1

        def meter(value):
            usage["responses"] += 1
            for key in ("input_tokens", "output_tokens"):
                usage[key] += value[key]

        items, _ = _provider.generate(
            task="Return suggestion 'omit' only if the snippet occurs exactly in another field; otherwise return 'keep'.",
            task_key="rag_dedup", lines=lines, before_attempt=reserve, on_usage=meter,
        )
        omit = set()
        for item in items:
            if item["suggestion"] not in {"keep", "omit"}:
                raise ValueError("invalid decision")
            if item["suggestion"] == "omit":
                if item["source_id"] not in eligible:
                    raise ValueError("evidence would be lost")
                omit.add(item["source_id"])
        result = _without_snippets(pack, omit)
        status = "applied" if omit else "unchanged"
        return result
    except Exception:
        return pack
    finally:
        log_event("ai.rag.offload", provider="groq", task="rag_dedup", status=status,
                  duration_ms=round((time.perf_counter() - started) * 1000, 2),
                  **usage, usage_complete=usage["attempts"] == usage["responses"],
                  context_chars_saved=len(pack.render_for_prompt()) - len(result.render_for_prompt()))
        _slots.release()


def _without_snippets(pack, ids):
    items = [replace(item, snippet="") if f"s{i}" in ids else item
             for i, item in enumerate(pack.items)]
    updated = replace(pack, items=items)
    return replace(updated, packed_context_chars=len(updated.render_for_prompt()))
