from pathlib import Path

from app.config import get_recipe_dataset_dir, get_recipe_dataset_index_limit, get_retrieval_cache_settings
from app.dataset_adapter import inspect_recipe_dataset, iter_recipe_dataset_records
from app.dataset_index import build_recipe_index, search_recipe_index
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_dataset_search_input
from app.retrieval_cache import (
    cache_metadata_for_index,
    get_cached_dataset_index,
    get_cached_retrieval_results,
    merge_cache_metadata,
)
from app.schemas import (
    DatasetCacheMetadata,
    DatasetIndexSummaryResponse,
    DatasetSearchProvenance,
    DatasetSearchResponse,
    DatasetSearchResult,
)



def search_dataset_recipes(query: str, limit: int = 10, dataset_limit: int | None = None) -> DatasetSearchResponse:
    input_quality = classify_dataset_search_input(query)
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return DatasetSearchResponse(
            query=query,
            count=0,
            results=[],
            index=empty_dataset_index_summary(dataset_limit or get_recipe_dataset_index_limit(), input_quality.warnings),
            warnings=input_quality.warnings,
            input_quality=input_quality.to_dict(),
            cache=empty_dataset_cache(),
        )

    dataset_dir = Path(get_recipe_dataset_dir())
    record_limit = dataset_limit or get_recipe_dataset_index_limit()
    warnings: list[str] = [*input_quality.warnings] if input_quality.status == WEAK_BUT_USABLE else []

    if not dataset_dir.exists():
        warnings.append("Configured recipe dataset directory does not exist.")
        index_summary = DatasetIndexSummaryResponse(
            document_count=0,
            source_counts={},
            fields_indexed=[],
            token_count=0,
            build_metadata={"mode": "in_memory", "input_records": 0, "dataset_dir": "configured", "record_limit": record_limit},
            warnings=warnings,
            cache=empty_dataset_cache(),
        )
        return DatasetSearchResponse(query=query, count=0, results=[], index=index_summary, warnings=warnings, input_quality=input_quality.to_dict(), cache=empty_dataset_cache())

    inspection = inspect_recipe_dataset(dataset_dir)
    warnings.extend(inspection.warnings)
    if _is_generated_demo_dataset(dataset_dir):
        warnings = _filter_generated_demo_warnings(warnings)

    index, index_cache, index_cache_key = get_cached_dataset_index(
        dataset_dir=dataset_dir,
        record_limit=record_limit,
        build_fn=lambda: build_recipe_index(iter_recipe_dataset_records(dataset_dir, limit=record_limit)),
    )
    summary_warnings = [*warnings, *index.summary.warnings]
    index_summary = DatasetIndexSummaryResponse(
        document_count=index.summary.document_count,
        source_counts=index.summary.source_counts,
        fields_indexed=index.summary.fields_indexed,
        token_count=index.summary.token_count,
        build_metadata={
            **index.summary.build_metadata,
            "dataset_dir": "configured",
            "record_limit": record_limit,
        },
        warnings=summary_warnings,
        cache=cache_metadata_for_index(index_cache),
    )

    if not query.strip():
        return DatasetSearchResponse(query=query, count=0, results=[], index=index_summary, warnings=summary_warnings, input_quality=input_quality.to_dict(), cache=index_cache)

    cached_results, retrieval_cache, _retrieval_cache_key = get_cached_retrieval_results(
        index_cache_key=index_cache_key,
        query=query,
        limit=limit,
        build_fn=lambda: search_recipe_index(index, query=query, limit=limit),
    )
    results = [
        DatasetSearchResult(
            id=result.id,
            source_id=result.source_id,
            title=result.title,
            score=result.score,
            matched_fields=result.matched_fields,
            snippet=result.snippet,
            source_file=result.source_file,
            source_table=result.source_table,
            provenance=DatasetSearchProvenance(
                source_file=result.source_file,
                source_table=result.source_table,
                source_id=result.source_id,
            ),
        )
        for result in cached_results
    ]

    return DatasetSearchResponse(
        query=query,
        count=len(results),
        results=results,
        index=index_summary,
        warnings=summary_warnings,
        input_quality=input_quality.to_dict(),
        cache=merge_cache_metadata(index_cache, retrieval_cache),
    )


def empty_dataset_index_summary(record_limit: int, warnings: list[str] | None = None) -> DatasetIndexSummaryResponse:
    return DatasetIndexSummaryResponse(
        document_count=0,
        source_counts={},
        fields_indexed=[],
        token_count=0,
        build_metadata={"mode": "input_quality", "input_records": 0, "dataset_dir": "not_inspected", "record_limit": record_limit},
        warnings=warnings or [],
        cache=empty_dataset_cache(),
    )


def empty_dataset_cache() -> DatasetCacheMetadata:
    settings = get_retrieval_cache_settings()
    return DatasetCacheMetadata(
        cache_enabled=settings.enabled,
        cache_max_entries=settings.max_entries,
        cache_ttl_seconds=settings.ttl_seconds,
    )


def _is_generated_demo_dataset(dataset_dir: Path) -> bool:
    marker = dataset_dir / ".ai-demo-fixture.json"
    if not marker.is_file():
        return False
    try:
        data = marker.read_text(encoding="utf-8")
    except OSError:
        return False
    return "cookbook-ai-demo-fixture" in data


def _filter_generated_demo_warnings(warnings: list[str]) -> list[str]:
    optional_missing = {
        "13k-recipes.db is missing.",
        "5k-recipes.db is missing.",
        "metadata.json is missing.",
        "README.md is missing.",
        "tutorial.md is missing.",
    }
    return [warning for warning in warnings if warning not in optional_missing]
