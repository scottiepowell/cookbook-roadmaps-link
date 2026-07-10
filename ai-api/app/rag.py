from dataclasses import dataclass

from app.ai_access_models import AiAccessWorkflow
from app.ai_budget_guard import check_provider_budget
from app.config import get_ai_settings
from app.config import get_provider_budget_settings
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_question_input
from app.providers import LLMProvider, LLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.recipe_reader import load_recipe_documents
from app.schemas import AskCitation, AskRequest, AskResponse, AskRetrievalMetadata, RecipeDocument
from app.search import search_recipes


ASK_SYSTEM_PROMPT = (
    "Answer only from the provided cookbook recipe context. "
    "If the context does not answer the question, say that the saved cookbook does not contain an answer. "
    "Do not invent recipes, ingredients, or instructions."
)

QUESTION_STOP_WORDS = {
    "a",
    "an",
    "and",
    "can",
    "do",
    "for",
    "i",
    "in",
    "is",
    "make",
    "me",
    "my",
    "of",
    "the",
    "to",
    "what",
    "which",
    "with",
}


class AskError(RuntimeError):
    """Base error for Ask My Cookbook failures."""


class AskProviderError(AskError):
    """Raised when the provider cannot synthesize an answer."""


@dataclass(frozen=True)
class RetrievedRecipe:
    document: RecipeDocument
    citation: AskCitation


def ask_cookbook(
    request: AskRequest,
    provider: LLMProvider | None = None,
    recipes: list[RecipeDocument] | None = None,
    session_state: object | None = None,
) -> AskResponse:
    settings = get_ai_settings()
    input_quality = classify_question_input(request.question)
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return AskResponse(
            answer=input_quality.clarifying_question or "I need a little more useful cookbook detail before searching saved recipes.",
            citations=[],
            provider="none",
            model="none",
            retrieval=AskRetrievalMetadata(query=request.question, retrieved_count=0, limit=request.limit, matched_recipe_ids=[]),
            warnings=input_quality.warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    documents = recipes if recipes is not None else load_recipe_documents()
    retrieved = retrieve_recipe_context(documents, request.question, request.limit)
    retrieval = AskRetrievalMetadata(
        query=request.question,
        retrieved_count=len(retrieved),
        limit=request.limit,
        matched_recipe_ids=[item.document.id for item in retrieved],
    )

    if not retrieved:
        return AskResponse(
            answer="I could not find a matching saved recipe for that question.",
            citations=[],
            provider="none",
            model="none",
            retrieval=retrieval,
            warnings=["No matching saved recipes were found; no provider call was made."],
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    provider_name = provider.name if provider is not None else settings.provider
    provider_model = getattr(provider, "model", None)
    if provider_model is None:
        provider_model = settings.openai_model if provider_name == "openai" else settings.model
    budget_decision = check_provider_budget(
        AiAccessWorkflow.ASK_MY_COOKBOOK,
        provider_name,
        provider_model,
        _estimate_input_tokens(request.question, retrieved),
        settings.max_output_tokens,
        session_state,
        get_provider_budget_settings(),
    )
    if not budget_decision.allowed:
        warnings = list(input_quality.warnings) if input_quality.status == WEAK_BUT_USABLE else []
        warnings.append(budget_decision.safe_message)
        return AskResponse(
            answer=budget_decision.safe_message,
            citations=[item.citation for item in retrieved],
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
                prompt=_build_prompt(request.question, retrieved),
                system=ASK_SYSTEM_PROMPT,
                max_output_tokens=settings.max_output_tokens,
                temperature=0,
            )
        )
    except ProviderError as exc:
        raise AskProviderError("Ask provider failed.") from exc

    return AskResponse(
        answer=provider_response.text,
        citations=[item.citation for item in retrieved],
        provider=provider_response.provider,
        model=provider_response.model,
        retrieval=retrieval,
        warnings=input_quality.warnings if input_quality.status == WEAK_BUT_USABLE else [],
        usage=provider_response.usage,
        input_quality=input_quality.to_dict(),
    )


def retrieve_recipe_context(
    recipes: list[RecipeDocument],
    question: str,
    limit: int,
) -> list[RetrievedRecipe]:
    by_id = {recipe.id: recipe for recipe in recipes}
    search_query = _retrieval_query(question)
    if not search_query:
        return []
    search_results = search_recipes(recipes, search_query, limit=limit)
    retrieved: list[RetrievedRecipe] = []
    for result in search_results:
        document = by_id.get(result.id)
        if document is None:
            continue
        retrieved.append(
            RetrievedRecipe(
                document=document,
                citation=AskCitation(
                    recipe_id=document.id,
                    title=document.title,
                    snippet=result.snippet or _recipe_snippet(document),
                ),
            )
        )
    return retrieved


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise AskProviderError("Ask provider is not configured.") from exc


def _build_prompt(question: str, retrieved: list[RetrievedRecipe]) -> str:
    context_blocks = []
    for index, item in enumerate(retrieved, start=1):
        recipe = item.document
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] Recipe ID: {recipe.id}",
                    f"Title: {recipe.title}",
                    f"Description: {recipe.description or ''}",
                    f"Ingredients: {'; '.join(recipe.ingredients)}",
                    f"Instructions: {'; '.join(recipe.instructions)}",
                    f"Tags: {'; '.join(recipe.tags)}",
                ]
            )
        )
    return f"Question: {question.strip()}\n\nRetrieved recipe context:\n\n" + "\n\n".join(context_blocks)


def _recipe_snippet(recipe: RecipeDocument) -> str:
    parts = [recipe.description or "", " ".join(recipe.ingredients), " ".join(recipe.instructions)]
    snippet = " ".join(part for part in parts if part).strip()
    return snippet[:180] if snippet else recipe.title


def _retrieval_query(question: str) -> str:
    tokens = [
        token
        for token in question.replace("?", " ").split()
        if token.lower().strip(".,:;!()[]{}") not in QUESTION_STOP_WORDS
    ]
    return " ".join(tokens)


def _estimate_input_tokens(question: str, retrieved: list[RetrievedRecipe]) -> int:
    prompt = _build_prompt(question, retrieved)
    return max(1, len(prompt.split()))
