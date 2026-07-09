from collections import Counter
from dataclasses import dataclass, field

from app.dataset_adapter import ExternalRecipeRecord, iter_recipe_dataset_records
from app.dataset_normalization import extract_phrases, normalize_index_text, normalize_text, safe_tokenize
from app.retrieval_cache import get_cached_dataset_index


INDEX_SCORING_VERSION = "2026-07-09"


FIELD_WEIGHTS = {
    "title": 12,
    "tags": 9,
    "ingredients": 6,
    "instructions": 4,
    "source": 1,
}

ANCHOR_FIELD_BONUS = {
    "title": 26,
    "tags": 18,
    "ingredients": 12,
    "instructions": 8,
    "source": 2,
}

QUERY_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "make",
    "maybe",
    "of",
    "or",
    "save",
    "the",
    "to",
    "with",
}

BROAD_QUERY_TERMS = {
    "bake",
    "butter",
    "cheese",
    "chicken",
    "cream",
    "cooked",
    "dessert",
    "dinner",
    "easy",
    "food",
    "hot",
    "meal",
    "mix",
    "pasta",
    "quick",
    "recipe",
    "rice",
    "soup",
    "sugar",
    "serve",
    "simple",
    "warm",
}

WEAK_MATCH_SCORE_THRESHOLD = 30


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
    normalized_title: str = ""
    normalized_ingredients: str = ""
    normalized_instructions: str = ""
    normalized_tags: str = ""
    phrases: list[str] = field(default_factory=list)
    aliases_applied: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IndexedRecipeDocument:
    document: IndexableRecipeDocument
    normalized_fields: dict[str, str]
    normalized_field_tokens: dict[str, list[str]]
    normalized_field_phrases: dict[str, list[str]]
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


@dataclass(frozen=True)
class RecipeQueryAnalysis:
    query: str
    tokens: list[str]
    phrases: list[str]
    strong_anchors: list[str]
    anchors: list[str]
    specific_terms: list[str]
    broad_terms: list[str]


def analyze_recipe_query(query: str) -> RecipeQueryAnalysis:
    tokens = safe_tokenize(query)
    phrases = extract_phrases(query)
    if not tokens:
        return RecipeQueryAnalysis(query=query, tokens=[], phrases=phrases, strong_anchors=[], anchors=[], specific_terms=[], broad_terms=[])

    meaningful_tokens = [token for token in tokens if token not in QUERY_STOP_WORDS]
    broad_terms = [token for token in meaningful_tokens if token in BROAD_QUERY_TERMS]
    specific_terms = [token for token in meaningful_tokens if token not in BROAD_QUERY_TERMS]
    strong_anchors = _dedupe_preserve_order(_infer_strong_dish_anchors(tokens, phrases))
    anchors = _dedupe_preserve_order(
        [
            *_infer_dish_anchors(tokens, phrases),
            *phrases,
            *_phrase_anchors(meaningful_tokens),
        ]
    )
    return RecipeQueryAnalysis(
        query=query,
        tokens=tokens,
        phrases=phrases,
        strong_anchors=strong_anchors,
        anchors=anchors,
        specific_terms=specific_terms,
        broad_terms=broad_terms,
    )


def build_index_from_dataset(dataset_dir: str | None = None, limit: int = 100) -> RecipeDatasetIndex:
    index, _, _ = get_cached_dataset_index(
        dataset_dir=dataset_dir,
        record_limit=limit,
        build_fn=lambda: build_recipe_index(iter_recipe_dataset_records(dataset_dir=dataset_dir, limit=limit)),
    )
    return index


def build_recipe_index(records: list[ExternalRecipeRecord]) -> RecipeDatasetIndex:
    indexed: list[IndexedRecipeDocument] = []
    source_counts: Counter[str] = Counter()
    token_count = 0

    for original_index, record in enumerate(records):
        document = normalize_external_record(record)
        normalized_fields = {
            "title": normalize_text(document.title),
            "tags": normalize_text(" ".join(document.tags)),
            "ingredients": normalize_text(" ".join(document.ingredients)),
            "instructions": normalize_text(" ".join(document.instructions)),
            "source": normalize_text(" ".join(value for value in (document.source_file, document.source_table or "") if value)),
        }
        normalized_field_tokens = {
            "title": normalize_index_text(document.title).tokens,
            "tags": normalize_index_text(" ".join(document.tags)).tokens,
            "ingredients": normalize_index_text(" ".join(document.ingredients)).tokens,
            "instructions": normalize_index_text(" ".join(document.instructions)).tokens,
            "source": normalize_index_text(" ".join(value for value in (document.source_file, document.source_table or "") if value)).tokens,
        }
        normalized_field_phrases = {
            "title": normalize_index_text(document.title).phrases,
            "tags": normalize_index_text(" ".join(document.tags)).phrases,
            "ingredients": normalize_index_text(" ".join(document.ingredients)).phrases,
            "instructions": normalize_index_text(" ".join(document.instructions)).phrases,
            "source": normalize_index_text(" ".join(value for value in (document.source_file, document.source_table or "") if value)).phrases,
        }
        token_count += sum(len(tokens) for tokens in normalized_field_tokens.values())
        source_counts[document.source_file] += 1
        indexed.append(
            IndexedRecipeDocument(
                document=document,
                normalized_fields=normalized_fields,
                normalized_field_tokens=normalized_field_tokens,
                normalized_field_phrases=normalized_field_phrases,
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
    analysis = analyze_recipe_query(query)
    if not analysis.tokens or limit <= 0:
        return []

    scored: list[tuple[RecipeIndexSearchResult, int]] = []
    for indexed in index.documents:
        result = _score_indexed_document(indexed, analysis)
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
    analysis: RecipeQueryAnalysis,
) -> RecipeIndexSearchResult | None:
    score = 0.0
    matched_fields: list[str] = []
    snippet: str | None = None
    broad_token_hits = 0
    specific_token_hits = 0

    for field, tokens in indexed.normalized_field_tokens.items():
        field_score = 0.0
        normalized_field_text = indexed.normalized_fields[field]
        field_phrases = indexed.normalized_field_phrases[field]
        for phrase in analysis.phrases:
            if not phrase or not _phrase_matches(phrase, normalized_field_text):
                continue
            if phrase in field_phrases:
                field_score += 2.5
            elif field in {"title", "ingredients"}:
                field_score += 2.0
            else:
                field_score += 1.2
            if field not in matched_fields:
                matched_fields.append(field)
        for token in analysis.tokens:
            if not _token_matches(token, tokens):
                continue
            if token in BROAD_QUERY_TERMS:
                field_score += 0.35
                broad_token_hits += 1
            else:
                field_score += 1.0
                specific_token_hits += 1
        if field_score == 0:
            continue
        score += field_score * FIELD_WEIGHTS[field]
        matched_fields.append(field)
        if snippet is None:
            snippet = _make_snippet(_field_text(indexed.document, field), analysis.tokens)

    anchor_bonus = 0.0
    for anchor in analysis.anchors:
        normalized_anchor = normalize_text(anchor)
        if not normalized_anchor:
            continue
        for field, field_text in indexed.normalized_fields.items():
            if not _phrase_matches(normalized_anchor, field_text):
                continue
            anchor_bonus += ANCHOR_FIELD_BONUS[field]
            if field == "title" and normalized_anchor == field_text:
                anchor_bonus += 18
            if field not in matched_fields:
                matched_fields.append(field)
            break

    if specific_token_hits == 0:
        score *= 0.55
        score -= broad_token_hits * 1.5
    else:
        score += specific_token_hits * 2
        if anchor_bonus == 0:
            score *= 0.9

    score += anchor_bonus

    if score <= 0:
        return None

    document = indexed.document
    return RecipeIndexSearchResult(
        id=document.id,
        source_id=document.source_id,
        title=document.title,
        score=int(round(score)),
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


def _phrase_matches(phrase: str, text: str) -> bool:
    if not phrase or not text:
        return False
    normalized_phrase = normalize_text(phrase)
    normalized_text = normalize_text(text)
    return f" {normalized_phrase} " in f" {normalized_text} "


def _infer_dish_anchors(tokens: list[str], phrases: list[str]) -> list[str]:
    token_set = set(tokens)
    phrase_set = set(phrases)
    anchors: list[str] = []

    if "cheesecake" in token_set or "baked cheesecake" in phrase_set or ({"cream", "cheese", "graham"} <= token_set):
        anchors.extend(
            [
                "cheesecake",
                "cream cheese",
                "graham cracker crust",
                "graham cracker",
                "crust",
                "bake",
                "chill",
            ]
        )

    if "carbonara" in token_set or ({"spaghetti", "parmesan", "pancetta"} <= token_set) or ({"eggs", "parmesan", "black", "pepper"} <= token_set):
        anchors.extend(
            [
                "carbonara",
                "spaghetti",
                "eggs",
                "parmesan",
                "pancetta",
                "black pepper",
                "pasta water",
                "off heat",
            ]
        )

    if "omelet" in token_set or "omelette" in token_set or {"eggs", "butter", "fold"} <= token_set or "omelet" in phrase_set:
        anchors.extend(
            [
                "omelet",
                "omelette",
                "eggs",
                "cheese",
                "onions",
                "butter",
                "fold",
                "scramble",
            ]
        )

    if "casserole" in token_set or "chicken and rice" in phrase_set or ({"chicken", "rice"} <= token_set):
        anchors.extend(
            [
                "chicken and rice casserole",
                "chicken",
                "rice",
                "casserole",
                "cream soup",
                "bake",
                "cheese",
            ]
        )

    return anchors


def _infer_strong_dish_anchors(tokens: list[str], phrases: list[str]) -> list[str]:
    token_set = set(tokens)
    phrase_set = set(phrases)
    anchors: list[str] = []

    if "cheesecake" in token_set or "baked cheesecake" in phrase_set:
        anchors.extend(["cheesecake", "cream cheese", "graham cracker crust", "graham cracker"])

    if "carbonara" in token_set or {"spaghetti", "pancetta"} <= token_set:
        anchors.extend(["carbonara", "spaghetti", "parmesan", "pancetta", "black pepper", "pasta water", "eggs"])

    if "omelet" in token_set or "omelette" in token_set or "omelet" in phrase_set:
        anchors.extend(["omelet", "omelette", "scramble", "fold"])

    if "casserole" in token_set or "chicken and rice" in phrase_set:
        anchors.extend(["chicken and rice casserole", "casserole", "cream soup"])

    if {"chicken", "rice"} <= token_set:
        anchors.extend(["chicken and rice casserole", "casserole", "cream soup"])

    return anchors


def _phrase_anchors(tokens: list[str]) -> list[str]:
    anchors: list[str] = []
    for size in (2, 3):
        for start in range(0, max(len(tokens) - size + 1, 0)):
            phrase = " ".join(tokens[start : start + size])
            if len(phrase) >= 5:
                anchors.append(phrase)
    return anchors[:8]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


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
