from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.dataset_adapter import ExternalRecipeRecord, iter_recipe_dataset_records
from app.dataset_index import WEAK_MATCH_SCORE_THRESHOLD
from app.schemas import DatasetSearchResult


DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES = 2
DEFAULT_IMPORTER_CONTEXT_MAX_CHARS = 2000
DEFAULT_IMPORTER_CONTEXT_MAX_SNIPPET_CHARS = 320
DEFAULT_IMPORTER_CONTEXT_MAX_INGREDIENT_CHARS = 320
DEFAULT_IMPORTER_CONTEXT_MAX_INSTRUCTION_CHARS = 360


@dataclass(frozen=True)
class PackedImporterContextExample:
    rank: int
    id: str
    title: str
    matched_fields: list[str]
    snippet: str
    key_ingredients: list[str]
    instruction_summary: str
    relevance_category: str
    score: int | None = None
    source_id: str | None = None


@dataclass(frozen=True)
class PackedImporterContext:
    query: str
    retrieved_count: int
    packed_count: int
    packed_ids: list[str] = field(default_factory=list)
    dropped_ids: list[str] = field(default_factory=list)
    max_examples: int = DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES
    max_context_chars: int = DEFAULT_IMPORTER_CONTEXT_MAX_CHARS
    packed_context_chars: int = 0
    weak_examples_included: bool = False
    context_budget_warning: str | None = None
    items: list[PackedImporterContextExample] = field(default_factory=list)

    def render_for_prompt(self) -> str:
        if not self.items:
            return (
                "\nRetrieved dataset examples: none available; rely on the user notes and general cooking structure only.\n"
            )

        lines = [
            "\nRetrieved dataset examples for structure only:",
            f"Use up to {len(self.items)} packed example(s); user intent controls the recipe.",
        ]
        if self.weak_examples_included:
            lines.append("The packed examples are weak matches and must be treated as structure-only guidance.")
        for item in self.items:
            quality_label = "weak/structure-only" if item.relevance_category == "weak" else item.relevance_category
            lines.extend(
                [
                    "",
                    f"Example {item.rank} [{quality_label}]: {item.title}",
                    f"Source id: {item.source_id or item.id}",
                    f"Matched fields: {', '.join(item.matched_fields) or 'none'}",
                    f"Key ingredients: {', '.join(item.key_ingredients) or 'none'}",
                    f"Instruction summary: {item.instruction_summary or 'none'}",
                    f"Snippet: {item.snippet or 'none'}",
                ]
            )
        if self.context_budget_warning:
            lines.extend(["", f"Context budget warning: {self.context_budget_warning}"])
        return "\n".join(lines).strip() + "\n"


def pack_importer_rag_context(
    query: str,
    results: list[DatasetSearchResult],
    *,
    dataset_dir: str | Path | None,
    dataset_limit: int | None,
    max_examples: int = DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES,
    max_context_chars: int = DEFAULT_IMPORTER_CONTEXT_MAX_CHARS,
    max_snippet_chars: int = DEFAULT_IMPORTER_CONTEXT_MAX_SNIPPET_CHARS,
    max_ingredient_chars: int = DEFAULT_IMPORTER_CONTEXT_MAX_INGREDIENT_CHARS,
    max_instruction_chars: int = DEFAULT_IMPORTER_CONTEXT_MAX_INSTRUCTION_CHARS,
) -> PackedImporterContext:
    if not results:
        return PackedImporterContext(
            query=query,
            retrieved_count=0,
            packed_count=0,
            max_examples=max_examples,
            max_context_chars=max_context_chars,
        )

    record_map = _record_map(dataset_dir, dataset_limit)
    scored_candidates = [
        (
            result,
            _classify_result_relevance(result.score),
        )
        for result in results
    ]
    strong_or_moderate = [item for item in scored_candidates if item[1] != "weak"]
    eligible = strong_or_moderate if strong_or_moderate else scored_candidates

    selected = eligible[:max_examples]
    weak_examples_included = any(category == "weak" for _, category in selected) and not strong_or_moderate

    items: list[PackedImporterContextExample] = []
    prompt_block = ""
    truncated_for_budget = False
    for rank, (result, category) in enumerate(selected, start=1):
        record = record_map.get(result.source_id)
        item = _make_item(
            rank=rank,
            result=result,
            category=category,
            record=record,
            max_snippet_chars=max_snippet_chars,
            max_ingredient_chars=max_ingredient_chars,
            max_instruction_chars=max_instruction_chars,
        )
        candidate_block = _render_item_block(item)
        if prompt_block and len(prompt_block) + len(candidate_block) > max_context_chars:
            truncated_for_budget = True
            break
        if not prompt_block and len(candidate_block) > max_context_chars:
            truncated_for_budget = True
            candidate_block = candidate_block[: max_context_chars - 3].rstrip() + "..."
        prompt_block += candidate_block
        items.append(item)

    packed_ids = [item.id for item in items]
    dropped_ids = [result.id for result, _ in scored_candidates if result.id not in packed_ids]
    budget_warning = None
    if truncated_for_budget:
        budget_warning = "Packed importer RAG context was truncated to fit the character budget."
    elif len(packed_ids) < len(selected):
        budget_warning = "Packed importer RAG context omitted lower-priority examples to stay within the character budget."

    return PackedImporterContext(
        query=query,
        retrieved_count=len(results),
        packed_count=len(items),
        packed_ids=packed_ids,
        dropped_ids=dropped_ids,
        max_examples=max_examples,
        max_context_chars=max_context_chars,
        packed_context_chars=len(prompt_block),
        weak_examples_included=weak_examples_included,
        context_budget_warning=budget_warning,
        items=items,
    )


def _record_map(
    dataset_dir: str | Path | None,
    dataset_limit: int | None,
) -> dict[str, ExternalRecipeRecord]:
    if dataset_dir is None:
        return {}
    records = iter_recipe_dataset_records(dataset_dir, limit=dataset_limit or 100)
    return {record.source_id: record for record in records}


def _make_item(
    *,
    rank: int,
    result: DatasetSearchResult,
    category: str,
    record: ExternalRecipeRecord | None,
    max_snippet_chars: int,
    max_ingredient_chars: int,
    max_instruction_chars: int,
) -> PackedImporterContextExample:
    key_ingredients = _truncate_list(
        list(record.ingredients) if record else [],
        max_ingredient_chars,
    )
    instruction_summary = _truncate_text(
        "; ".join(list(record.instructions)[:2]) if record else "",
        max_instruction_chars,
    )
    snippet = _truncate_text(result.snippet or result.title, max_snippet_chars)
    return PackedImporterContextExample(
        rank=rank,
        id=result.id,
        title=result.title,
        matched_fields=list(result.matched_fields),
        snippet=snippet,
        key_ingredients=key_ingredients,
        instruction_summary=instruction_summary,
        relevance_category=category,
        score=result.score,
        source_id=result.source_id,
    )


def _render_item_block(item: PackedImporterContextExample) -> str:
    return "\n".join(
        [
            f"Example {item.rank} [{item.relevance_category}]: {item.title}",
            f"Source id: {item.source_id or item.id}",
            f"Matched fields: {', '.join(item.matched_fields) or 'none'}",
            f"Key ingredients: {', '.join(item.key_ingredients) or 'none'}",
            f"Instruction summary: {item.instruction_summary or 'none'}",
            f"Snippet: {item.snippet or 'none'}",
        ]
    )


def _classify_result_relevance(score: int) -> str:
    if score >= int(WEAK_MATCH_SCORE_THRESHOLD * 1.5):
        return "strong"
    if score >= WEAK_MATCH_SCORE_THRESHOLD:
        return "moderate"
    return "weak"


def _truncate_list(values: list[str], max_chars: int) -> list[str]:
    cleaned: list[str] = []
    total = 0
    for value in values:
        truncated = _truncate_text(value, max_chars)
        if not truncated:
            continue
        next_total = total + len(truncated) + (2 if cleaned else 0)
        if next_total > max_chars:
            break
        cleaned.append(truncated)
        total = next_total
    return cleaned


def _truncate_text(value: str, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + "..."
