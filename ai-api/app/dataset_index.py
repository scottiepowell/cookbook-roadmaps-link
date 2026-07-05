import re
from collections import Counter
from dataclasses import dataclass, field

from app.dataset_adapter import ExternalRecipeRecord, iter_recipe_dataset_records


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

FIELD_WEIGHTS = {
    "title": 10,
    "tags": 8,
    "ingredients": 5,
    "instructions": 3,
    "source": 1,
}


@dataclass(frozen=True)
class IndexableRecipeDocument:
    id: str
    source_id: str
    title: str
    ingredients: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_file: str = ""
    source_table: str | None = None


@dataclass(frozen=True)
class IndexedRecipeDocument:
    document: IndexableRecipeDocument
    field_tokens: dict[str, list[str]]
    original_index: int


@dataclass(frozen=True)
class RecipeIndexSummary:
    document_count: int
    source_counts: dict[str, int]
    fields_indexed: list[str]
    token_count: int
    build_metadata: dict[str, str | int]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecipeDatasetIndex:
    documents: list[IndexedRecipeDocument]
    summary: RecipeIndexSummary


@dataclass(frozen=True)
class RecipeIndexSearchResult:
    id: str
    source_id: str
    title: str
    score: int
    matched_fields: list[str]
    snippet: str | None
    source_file: str
    source_table: str | None = None


def build_index_from_dataset(dataset_dir: str | None = None, limit: int = 100) -> RecipeDatasetIndex:
    return build_recipe_index(iter_recipe_dataset_records(dataset_dir=dataset_dir, limit=limit))


def build_recipe_index(records: list[ExternalRecipeRecord]) -> RecipeDatasetIndex:
    indexed: list[IndexedRecipeDocument] = []
    source_counts: Counter[str] = Counter()
    token_count = 0

    for original_index, record in enumerate(records):
        document = normalize_external_record(record)
        field_tokens = {
            "title": _tokenize(document.title),
            "tags": _tokenize(" ".join(document.tags)),
            "ingredients": _tokenize(" ".join(document.ingredients)),
            "instructions": _tokenize(" ".join(document.instructions)),
            "source": _tokenize(" ".join(value for value in (document.source_file, document.source_table or "") if value)),
        }
        token_count += sum(len(tokens) for tokens in field_tokens.values())
        source_counts[document.source_file] += 1
        indexed.append(
            IndexedRecipeDocument(
                document=document,
                field_tokens=field_tokens,
                original_index=original_index,
            )
        )

    return RecipeDatasetIndex(
        documents=indexed,
        summary=RecipeIndexSummary(
            document_count=len(indexed),
            source_counts=dict(sorted(source_counts.items())),
            fields_indexed=list(FIELD_WEIGHTS.keys()),
            token_count=token_count,
            build_metadata={"mode": "in_memory", "input_records": len(records)},
            warnings=[],
        ),
    )


def search_recipe_index(index: RecipeDatasetIndex, query: str, limit: int = 10) -> list[RecipeIndexSearchResult]:
    query_tokens = _tokenize(query)
    if not query_tokens or limit <= 0:
        return []

    scored: list[tuple[RecipeIndexSearchResult, int]] = []
    for indexed in index.documents:
        result = _score_indexed_document(indexed, query_tokens)
        if result is not None:
            scored.append((result, indexed.original_index))

    scored.sort(key=lambda item: (-item[0].score, item[1], item[0].id))
    return [result for result, _ in scored[:limit]]


def normalize_external_record(record: ExternalRecipeRecord) -> IndexableRecipeDocument:
    source = record.source_file
    if record.source_table:
        source = f"{source}:{record.source_table}"
    return IndexableRecipeDocument(
        id=f"{source}:{record.source_id}",
        source_id=record.source_id,
        title=record.title,
        ingredients=list(record.ingredients),
        instructions=list(record.instructions),
        tags=list(record.tags),
        source_file=record.source_file,
        source_table=record.source_table,
    )


def _score_indexed_document(
    indexed: IndexedRecipeDocument,
    query_tokens: list[str],
) -> RecipeIndexSearchResult | None:
    score = 0
    matched_fields: list[str] = []
    snippet: str | None = None

    for field, tokens in indexed.field_tokens.items():
        field_score = sum(1 for token in query_tokens if _token_matches(token, tokens))
        if field_score == 0:
            continue
        score += field_score * FIELD_WEIGHTS[field]
        matched_fields.append(field)
        if snippet is None:
            snippet = _make_snippet(_field_text(indexed.document, field), query_tokens)

    if score == 0:
        return None

    document = indexed.document
    return RecipeIndexSearchResult(
        id=document.id,
        source_id=document.source_id,
        title=document.title,
        score=score,
        matched_fields=matched_fields,
        snippet=snippet,
        source_file=document.source_file,
        source_table=document.source_table,
    )


def _field_text(document: IndexableRecipeDocument, field: str) -> str:
    if field == "title":
        return document.title
    if field == "tags":
        return " ".join(document.tags)
    if field == "ingredients":
        return " ".join(document.ingredients)
    if field == "instructions":
        return " ".join(document.instructions)
    if field == "source":
        return " ".join(value for value in (document.source_file, document.source_table or "") if value)
    return ""


def _tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


def _token_matches(query_token: str, field_tokens: list[str]) -> bool:
    return any(
        field_token == query_token
        or field_token.startswith(query_token)
        or query_token.startswith(field_token)
        for field_token in field_tokens
    )


def _make_snippet(value: str, query_tokens: list[str]) -> str:
    compact = " ".join(value.split())
    lowered = compact.lower()
    first_match = min(
        (lowered.find(token) for token in query_tokens if lowered.find(token) >= 0),
        default=0,
    )
    start = max(first_match - 40, 0)
    end = min(start + 140, len(compact))
    snippet = compact[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(compact):
        snippet = f"{snippet}..."
    return snippet
