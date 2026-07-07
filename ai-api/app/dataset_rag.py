from app.config import get_ai_settings, get_recipe_dataset_index_limit
from app.dataset_retrieval import empty_dataset_index_summary, search_dataset_recipes
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_dataset_question_input
from app.providers import LLMProvider, LLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.schemas import (
    DatasetAskCitation,
    DatasetAskRequest,
    DatasetAskResponse,
    DatasetAskRetrievalMetadata,
    DatasetSearchResult,
)


DATASET_ASK_SYSTEM_PROMPT = (
    "Answer only from the provided indexed recipe dataset context. "
    "Cite source IDs and titles. "
    "Do not invent recipes, ingredients, instructions, or source records. "
    "If the retrieved context is insufficient, say the indexed dataset does not contain enough information. "
    "Do not provide medical or nutrition certainty claims. "
    "Do not claim exact calories or macros unless present in the retrieved record context."
)

QUESTION_STOP_WORDS = {
    "a",
    "an",
    "and",
    "can",
    "dataset",
    "do",
    "for",
    "i",
    "in",
    "indexed",
    "is",
    "me",
    "of",
    "recipe",
    "the",
    "to",
    "uses",
    "what",
    "which",
    "with",
}


class DatasetAskError(RuntimeError):
    """Base error for dataset ask failures."""


class DatasetAskProviderError(DatasetAskError):
    """Raised when the provider cannot synthesize a dataset answer."""


def ask_dataset_recipes(
    request: DatasetAskRequest,
    provider: LLMProvider | None = None,
) -> DatasetAskResponse:
    dataset_limit = request.dataset_limit or get_recipe_dataset_index_limit()
    input_quality = classify_dataset_question_input(request.question)
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return DatasetAskResponse(
            answer=input_quality.clarifying_question or "I need a more useful dataset question before searching indexed recipes.",
            citations=[],
            provider="none",
            model="none",
            retrieval=DatasetAskRetrievalMetadata(
                query=request.question,
                retrieved_count=0,
                limit=request.limit,
                dataset_limit=dataset_limit,
                matched_result_ids=[],
                index=empty_dataset_index_summary(dataset_limit, input_quality.warnings),
            ),
            warnings=input_quality.warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    search_query = _retrieval_query(request.question)
    if not search_query:
        search_query = request.question

    retrieval_response = search_dataset_recipes(
        query=search_query,
        limit=request.limit,
        dataset_limit=dataset_limit,
    )
    citations = [_citation_from_result(result) for result in retrieval_response.results]
    retrieval = DatasetAskRetrievalMetadata(
        query=request.question,
        retrieved_count=len(citations),
        limit=request.limit,
        dataset_limit=dataset_limit,
        matched_result_ids=[citation.id for citation in citations],
        index=retrieval_response.index,
    )

    if not citations:
        warnings = [*retrieval_response.warnings]
        warnings.append("No matching indexed dataset recipes were found; no provider call was made.")
        return DatasetAskResponse(
            answer="I could not find a matching recipe in the indexed dataset.",
            citations=[],
            provider="none",
            model="none",
            retrieval=retrieval,
            warnings=warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    active_provider = provider or _get_configured_provider()
    try:
        provider_response = active_provider.generate_text(
            LLMRequest(
                prompt=_build_prompt(request.question, retrieval_response.results),
                system=DATASET_ASK_SYSTEM_PROMPT,
                max_output_tokens=get_ai_settings().max_output_tokens,
                temperature=0,
            )
        )
    except ProviderError as exc:
        raise DatasetAskProviderError("Dataset ask provider failed.") from exc

    return DatasetAskResponse(
        answer=provider_response.text,
        citations=citations,
        provider=provider_response.provider,
        model=provider_response.model,
        retrieval=retrieval,
        warnings=[*retrieval_response.warnings, *input_quality.warnings] if input_quality.status == WEAK_BUT_USABLE else retrieval_response.warnings,
        usage=provider_response.usage,
        input_quality=input_quality.to_dict(),
    )


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise DatasetAskProviderError("Dataset ask provider is not configured.") from exc


def _citation_from_result(result: DatasetSearchResult) -> DatasetAskCitation:
    return DatasetAskCitation(
        id=result.id,
        source_id=result.source_id,
        title=result.title,
        snippet=result.snippet or result.title,
        matched_fields=result.matched_fields,
        provenance=result.provenance,
    )


def _build_prompt(question: str, results: list[DatasetSearchResult]) -> str:
    context_blocks = []
    for index, result in enumerate(results, start=1):
        provenance = result.provenance
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] Dataset Result ID: {result.id}",
                    f"Source ID: {result.source_id}",
                    f"Title: {result.title}",
                    f"Snippet: {result.snippet or result.title}",
                    f"Matched fields: {', '.join(result.matched_fields)}",
                    f"Source file: {result.source_file}",
                    f"Source table: {result.source_table or ''}",
                    f"Dataset: {provenance.dataset}",
                    f"License: {provenance.license}",
                ]
            )
        )
    return f"Question: {question.strip()}\n\nRetrieved indexed dataset context:\n\n" + "\n\n".join(context_blocks)


def _retrieval_query(question: str) -> str:
    tokens = [
        token.strip(".,:;!()[]{}").lower()
        for token in question.replace("?", " ").split()
    ]
    return " ".join(token for token in tokens if token and token not in QUESTION_STOP_WORDS)
