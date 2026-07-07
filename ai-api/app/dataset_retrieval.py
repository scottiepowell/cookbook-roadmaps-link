from pathlib import Path

from app.config import get_recipe_dataset_dir, get_recipe_dataset_index_limit
from app.dataset_adapter import inspect_recipe_dataset, iter_recipe_dataset_records
from app.dataset_index import build_recipe_index, search_recipe_index
from app.schemas import (
    DatasetIndexSummaryResponse,
    DatasetSearchProvenance,
    DatasetSearchResponse,
    DatasetSearchResult,
)



def search_dataset_recipes(query: str, limit: int = 10, dataset_limit: int | None = None) -> DatasetSearchResponse:
    dataset_dir = Path(get_recipe_dataset_dir())
    record_limit = dataset_limit or get_recipe_dataset_index_limit()
    warnings: list[str] = []

    if not dataset_dir.exists():
        warnings.append("Configured recipe dataset directory does not exist.")
        index_summary = DatasetIndexSummaryResponse(
            document_count=0,
            source_counts={},
            fields_indexed=[],
            token_count=0,
            build_metadata={"mode": "in_memory", "input_records": 0, "dataset_dir": "configured", "record_limit": record_limit},
            warnings=warnings,
        )
        return DatasetSearchResponse(query=query, count=0, results=[], index=index_summary, warnings=warnings)

    inspection = inspect_recipe_dataset(dataset_dir)
    warnings.extend(inspection.warnings)
    if _is_generated_demo_dataset(dataset_dir):
        warnings = _filter_generated_demo_warnings(warnings)

    records = iter_recipe_dataset_records(dataset_dir, limit=record_limit)
    index = build_recipe_index(records)
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
    )

    if not query.strip():
        return DatasetSearchResponse(query=query, count=0, results=[], index=index_summary, warnings=summary_warnings)

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
        for result in search_recipe_index(index, query=query, limit=limit)
    ]

    return DatasetSearchResponse(
        query=query,
        count=len(results),
        results=results,
        index=index_summary,
        warnings=summary_warnings,
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
