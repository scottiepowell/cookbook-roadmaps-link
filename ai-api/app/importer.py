import re

from pydantic import ValidationError

from app.ai_access_models import AiAccessWorkflow
from app.ai_budget_guard import check_provider_budget
from app.config import get_ai_settings, get_recipe_dataset_dir
from app.config import get_provider_budget_settings
from app.dataset_index import WEAK_MATCH_SCORE_THRESHOLD, analyze_recipe_query
from app.dataset_retrieval import search_dataset_recipes
from app.input_quality import NEEDS_CLARIFICATION, REJECTED, WEAK_BUT_USABLE, classify_recipe_import_input
from app.rag_context import (
    DEFAULT_IMPORTER_CONTEXT_MAX_CHARS,
    DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES,
    PackedImporterContext,
    pack_importer_rag_context,
)
from app.rag_support_policy import assess_importer_rag_support
from app.providers import LLMProvider, StructuredLLMRequest, get_provider
from app.providers.errors import ProviderConfigError, ProviderError
from app.schemas import (
    RecipeImportCitation,
    RecipeImportDraft,
    RecipeImportRequest,
    RecipeImportResponse,
    RecipeImportRetrievalMetadata,
)


IMPORTER_SYSTEM_PROMPT = (
    "Import or create a practical structured recipe draft from rough user notes. Return only fields that fit the provided schema. "
    "Default to 4 servings unless the user states a different serving size. "
    "Provide plausible ingredient quantities for the serving size when the user omitted quantities, and disclose estimates in notes. "
    "Use retrieved dataset examples only for structure, proportions, and step completeness. "
    "Preserve the user's core ingredients and dish intent. Do not copy retrieved recipes verbatim. "
    "Do not add unrelated major ingredients, do not invent database IDs, and do not write to any database. "
    "Use 4 to 8 concise, action-oriented steps for normal multi-step recipes. "
    "Omelets should beat or scramble eggs before cooking and folding. "
    "Carbonara should not require heavy cream unless the user supplied it. "
    "Cheesecake should cover crust, filling, bake, cool, and chill. "
    "Chicken dishes should include safe doneness or temperature guidance when relevant."
)

IMPORTER_RAG_LIMIT = 3


class RecipeImporterError(RuntimeError):
    """Base error for recipe importer failures."""


class RecipeImportValidationError(RecipeImporterError):
    """Raised when provider output cannot be validated as a recipe draft."""


class RecipeImportProviderError(RecipeImporterError):
    """Raised when the configured provider cannot produce an importer draft."""


def import_recipe_text(
    request: RecipeImportRequest,
    provider: LLMProvider | None = None,
    session_state: object | None = None,
) -> RecipeImportResponse:
    settings = get_ai_settings()
    input_quality = classify_recipe_import_input(request.text)
    if input_quality.status in {NEEDS_CLARIFICATION, REJECTED}:
        return RecipeImportResponse(
            draft=None,
            provider="none",
            model="none",
            warnings=input_quality.warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )

    retrieval, citations, retrieval_warnings, context_pack = _retrieve_importer_examples(request.text)
    support = assess_importer_rag_support(
        relevance_category=retrieval.relevance_category if retrieval else None,
        retrieved_count=retrieval.retrieved_count if retrieval else 0,
        citation_count=len(citations),
        packed_count=retrieval.packed_count if retrieval else 0,
        weak_examples_included=retrieval.weak_examples_included if retrieval else False,
        matched_result_scores=retrieval.matched_result_scores if retrieval else None,
        warning=retrieval.warning if retrieval else None,
        top_k_relevant_count=_top_k_relevant_count(retrieval.matched_result_scores if retrieval else []),
    )
    provider_name = provider.name if provider is not None else settings.provider
    provider_model = getattr(provider, "model", None)
    if provider_model is None:
        provider_model = settings.openai_model if provider_name == "openai" else settings.model
    budget_decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        provider_name,
        provider_model,
        _estimate_input_tokens(request.text, citations, context_pack),
        settings.max_output_tokens,
        session_state,
        get_provider_budget_settings(),
    )
    if not budget_decision.allowed:
        warnings = [*retrieval_warnings]
        if input_quality.status == WEAK_BUT_USABLE:
            warnings.extend(input_quality.warnings)
        warnings.append(budget_decision.safe_message)
        return RecipeImportResponse(
            draft=None,
            provider="none",
            model="none",
            retrieval=retrieval,
            citations=citations,
            warnings=warnings,
            usage=None,
            input_quality=input_quality.to_dict(),
        )
    active_provider = provider or _get_configured_provider()
    schema = RecipeImportDraft.model_json_schema()
    try:
        provider_response = active_provider.generate_structured(
            StructuredLLMRequest(
                prompt=_build_prompt(
                    request,
                    citations,
                    retrieval.warning if retrieval else None,
                    support=support,
                    context_pack=context_pack,
                ),
                system=IMPORTER_SYSTEM_PROMPT,
                schema_name="RecipeImportDraft",
                schema=schema,
                max_output_tokens=get_ai_settings().max_output_tokens,
            )
        )
    except ProviderError as exc:
        raise RecipeImportProviderError("Recipe importer provider failed.") from exc

    try:
        draft = RecipeImportDraft.model_validate(provider_response.data)
    except ValidationError as exc:
        raise RecipeImportValidationError("Provider returned an invalid recipe draft.") from exc

    draft = _improve_draft(draft, request.text)
    warnings = [*retrieval_warnings]
    if input_quality.status == WEAK_BUT_USABLE:
        warnings.extend(input_quality.warnings)
    return RecipeImportResponse(
        draft=draft,
        provider=provider_response.provider,
        model=provider_response.model,
        retrieval=retrieval,
        citations=citations,
        warnings=warnings,
        usage=provider_response.usage,
        input_quality=input_quality.to_dict(),
    )


def _get_configured_provider() -> LLMProvider:
    try:
        return get_provider()
    except ProviderConfigError as exc:
        raise RecipeImportProviderError("Recipe importer provider is not configured.") from exc


def _retrieve_importer_examples(
    text: str,
) -> tuple[RecipeImportRetrievalMetadata | None, list[RecipeImportCitation], list[str], PackedImporterContext | None]:
    analysis = analyze_recipe_query(text)
    retrieval_response = search_dataset_recipes(text, limit=IMPORTER_RAG_LIMIT)
    citations = [
        RecipeImportCitation(
            id=result.id,
            source_id=result.source_id,
            title=result.title,
            snippet=result.snippet or result.title,
            matched_fields=result.matched_fields,
            provenance=result.provenance,
        )
        for result in retrieval_response.results[:IMPORTER_RAG_LIMIT]
    ]
    dataset_limit = int(retrieval_response.index.build_metadata.get("record_limit", 0) or 0)
    scores = [result.score for result in retrieval_response.results[:IMPORTER_RAG_LIMIT]]
    relevance_category, warning = _importer_relevance_category(citations, scores, analysis)
    context_pack = pack_importer_rag_context(
        text,
        retrieval_response.results[:IMPORTER_RAG_LIMIT],
        dataset_dir=get_recipe_dataset_dir(),
        dataset_limit=dataset_limit or None,
        max_examples=DEFAULT_IMPORTER_CONTEXT_MAX_EXAMPLES,
        max_context_chars=DEFAULT_IMPORTER_CONTEXT_MAX_CHARS,
    )
    support = assess_importer_rag_support(
        relevance_category=relevance_category,
        retrieved_count=len(citations),
        citation_count=len(citations),
        packed_count=context_pack.packed_count,
        weak_examples_included=context_pack.weak_examples_included,
        matched_result_scores=scores,
        warning=warning,
        top_k_relevant_count=_top_k_relevant_count(scores),
    )
    retrieval = RecipeImportRetrievalMetadata(
        query=text.strip(),
        retrieved_count=len(citations),
        limit=IMPORTER_RAG_LIMIT,
        dataset_limit=dataset_limit,
        matched_result_ids=[citation.id for citation in citations],
        anchors_used=analysis.anchors,
        matched_result_scores=scores,
        relevance_category=relevance_category,
        warning=warning,
        packed_count=context_pack.packed_count,
        packed_ids=context_pack.packed_ids,
        dropped_ids=context_pack.dropped_ids,
        max_examples=context_pack.max_examples,
        max_context_chars=context_pack.max_context_chars,
        packed_context_chars=context_pack.packed_context_chars,
        weak_examples_included=context_pack.weak_examples_included,
        context_budget_warning=context_pack.context_budget_warning,
        support_level=support.support_level,
        support_reason=support.support_reason,
        citation_support_count=support.citation_support_count,
        weak_citation_count=support.weak_citation_count,
        strong_citation_count=support.strong_citation_count,
        support_message=support.support_message,
        should_claim_rag_grounded=support.should_claim_rag_grounded,
        should_show_weak_support_warning=support.should_show_weak_support_warning,
        cache=retrieval_response.cache,
        index=retrieval_response.index,
    )
    warnings = list(retrieval_response.warnings)
    if warning:
        warnings.append(warning)
    if context_pack.context_budget_warning:
        warnings.append(context_pack.context_budget_warning)
    return retrieval, citations, warnings, context_pack


def _build_prompt(
    request: RecipeImportRequest,
    citations: list[RecipeImportCitation] | None = None,
    retrieval_warning: str | None = None,
    *,
    support=None,
    context_pack=None,
) -> str:
    source_line = f"Source: {request.source.strip()}\n" if request.source and request.source.strip() else ""
    example_context = context_pack.render_for_prompt() if context_pack is not None else _format_retrieved_examples(citations or [])
    if support is not None:
        retrieval_note = f"\nRAG support: {support.support_message}\n"
    else:
        retrieval_note = (
            "\nRetrieval note: Retrieved examples were weak matches; rely primarily on the user's notes and general recipe structure.\n"
            if retrieval_warning
            else ""
        )
    return (
        f"{source_line}Recipe text:\n{request.text.strip()}\n\n"
        "Creation requirements:\n"
        "- Make a complete, practical recipe draft for the requested dish.\n"
        "- Use 4 servings unless the user states a different serving size.\n"
        "- Estimate missing quantities for the serving size and disclose this in notes.\n"
        "- Preserve user-provided core ingredients and dish intent.\n"
        "- Do not copy retrieved examples verbatim; use them only for structure, proportions, and step completeness.\n"
        "- If retrieved examples are weak matches, rely primarily on the user's notes and general recipe structure.\n"
        "- Avoid unrelated major ingredients.\n"
        "- Prefer 4 to 8 action-oriented steps for multi-step dishes.\n"
        "- Omelet: beat/scramble eggs before cooking and folding.\n"
        "- Carbonara: avoid heavy cream unless supplied by the user.\n"
        "- Cheesecake: include crust, filling, bake, cool, and chill style steps.\n"
        "- Chicken casserole: include preheat, combine, bake, and doneness or safe chicken guidance.\n"
        f"{retrieval_note}"
        f"{example_context}"
    )


def _format_retrieved_examples(citations: list[RecipeImportCitation]) -> str:
    if not citations:
        return "\nRetrieved dataset examples: none available; rely on the user notes and general cooking structure.\n"
    blocks = ["\nRetrieved dataset examples for structure only:"]
    for index, citation in enumerate(citations[:IMPORTER_RAG_LIMIT], start=1):
        blocks.append(
            "\n".join(
                [
                    f"Example {index}: {citation.title}",
                    f"Source id: {citation.source_id}",
                    f"Matched fields: {', '.join(citation.matched_fields) or 'none'}",
                    f"Snippet: {citation.snippet}",
                ]
            )
        )
    return "\n\n" + "\n\n".join(blocks) + "\n"


def _importer_relevance_category(
    citations: list[RecipeImportCitation],
    scores: list[int],
    analysis,
) -> tuple[str, str | None]:
    if not citations:
        return "unavailable", "Importer dataset RAG examples were unavailable; created the draft from user notes only."

    strongest_score = scores[0] if scores else 0
    high_value_anchors = analysis.strong_anchors or analysis.anchors[:4]
    strong_anchor_match = any(
        _citation_contains_anchor(citation, anchor)
        for citation in citations
        for anchor in high_value_anchors
    )

    if strong_anchor_match and strongest_score >= WEAK_MATCH_SCORE_THRESHOLD:
        return "strong", None
    if strongest_score >= WEAK_MATCH_SCORE_THRESHOLD * 1.5:
        return "moderate", None
    return "weak", "Retrieved examples were weak matches; recipe draft was primarily shaped by user-provided notes and general recipe structure."


def _top_k_relevant_count(scores: list[int]) -> int | None:
    if not scores:
        return None
    return sum(1 for score in scores if score >= WEAK_MATCH_SCORE_THRESHOLD)



def _citation_contains_anchor(citation: RecipeImportCitation, anchor: str) -> bool:
    anchor_text = anchor.lower().strip()
    if not anchor_text:
        return False
    combined = " ".join(
        value for value in (citation.title, citation.snippet, citation.source_id) if value
    ).lower()
    return anchor_text in combined


def _improve_draft(draft: RecipeImportDraft, user_text: str) -> RecipeImportDraft:
    text = user_text.lower()
    servings = _servings_from_text(user_text) or 4
    updates = {"servings": servings}
    ingredients = [_ingredient_with_quantity(item, text, servings) for item in draft.ingredients]
    updates["ingredients"] = ingredients
    instructions = draft.instructions
    if "omelet" in text or "omelette" in text:
        instructions = _instruction_set(
            [
                "Beat the eggs with a pinch of salt and pepper until blended.",
                "Melt butter in a nonstick skillet over medium heat.",
                "Pour in the eggs and gently stir until soft curds form.",
                "Add cheese and onions if using, then fold the omelet and serve warm.",
            ]
        )
    elif "cheesecake" in text:
        instructions = _instruction_set(
            [
                "Preheat the oven and press the graham cracker crust into the pan.",
                "Beat cream cheese, sugar, vanilla, and eggs until smooth.",
                "Pour the filling into the crust and bake until the center is just set.",
                "Cool the cheesecake gradually, then chill until firm before slicing.",
            ]
        )
    elif "chicken" in text and "rice" in text and "casserole" in text:
        instructions = _instruction_set(
            [
                "Preheat the oven and grease a casserole dish.",
                "Combine rice, soup, cheese, and seasoning in the dish.",
                "Fold in chicken and enough liquid for the rice to cook evenly.",
                "Cover and bake until rice is tender and chicken reaches 165 F if raw chicken is used.",
                "Rest briefly before serving.",
            ]
        )
    elif _is_weak_instruction_set(instructions):
        instructions = _expand_generic_steps(instructions)
    updates["instructions"] = instructions
    notes = draft.notes or ""
    if _user_omitted_quantities(user_text) and "estimated" not in notes.lower():
        notes = (notes + " " if notes else "") + f"Ingredient quantities are estimated for {servings} servings because the source notes did not specify exact amounts."
    updates["notes"] = notes or None
    return draft.model_copy(update=updates)


def _estimate_input_tokens(
    user_text: str,
    citations: list[RecipeImportCitation],
    context_pack: PackedImporterContext | None,
) -> int:
    request = RecipeImportRequest(text=user_text)
    prompt = _build_prompt(
        request,
        citations,
        context_pack=context_pack,
    )
    return max(1, len(prompt.split()))


def _servings_from_text(text: str) -> int | None:
    match = re.search(r"\b(?:serves|servings?|for)\s+(\d{1,2})\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = int(match.group(1))
    if 1 <= value <= 24:
        return value
    return None


def _ingredient_with_quantity(item, text: str, servings: int):
    if item.quantity:
        return item
    estimate = _estimated_quantity(item.name, text, servings)
    if estimate is None:
        return item
    quantity, unit = estimate
    note = item.note or "estimated"
    return item.model_copy(update={"quantity": quantity, "unit": unit, "note": note})


def _estimated_quantity(name: str, text: str, servings: int) -> tuple[str, str] | None:
    lower = name.lower()
    scale = max(servings / 4, 0.25)
    if "egg" in lower:
        return (str(round(4 * scale)), "large")
    if "cheese" in lower or "parmesan" in lower:
        return (_scaled_fraction(1, scale), "cup")
    if "onion" in lower:
        return (_scaled_fraction(0.5, scale), "cup")
    if "butter" in lower or "oil" in lower:
        return (str(round(2 * scale)), "tablespoons")
    if "pasta" in lower or "spaghetti" in lower:
        return (str(round(12 * scale)), "ounces")
    if "pancetta" in lower or "bacon" in lower:
        return (str(round(4 * scale)), "ounces")
    if "cream cheese" in lower:
        return (str(round(16 * scale)), "ounces")
    if "sugar" in lower:
        return (_scaled_fraction(0.75, scale), "cup")
    if "graham" in lower or "crust" in lower:
        return (_scaled_fraction(1.5, scale), "cups")
    if "chicken" in lower:
        return (str(round(1.5 * scale, 1)), "pounds")
    if "rice" in lower:
        return (_scaled_fraction(1, scale), "cup")
    if "soup" in lower:
        return (str(round(1 * scale)), "can")
    if any(term in lower for term in ("bean", "chickpea")):
        return (str(round(2 * scale)), "cups")
    if "lemon" in lower:
        return (str(round(1 * scale)), "medium")
    if "garlic" in lower:
        return (str(round(2 * scale)), "cloves")
    if any(term in lower for term in ("parsley", "herb", "basil")):
        return (_scaled_fraction(0.25, scale), "cup")
    if "toast" in lower or "bread" in lower:
        return (str(round(4 * scale)), "slices")
    return None


def _scaled_fraction(value: float, scale: float) -> str:
    scaled = value * scale
    if scaled.is_integer():
        return str(int(scaled))
    return str(round(scaled, 2)).rstrip("0").rstrip(".")


def _user_omitted_quantities(text: str) -> bool:
    return not bool(re.search(r"\b\d+(?:/\d+)?\b|\b(cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|ounce|ounces|oz|pound|pounds|lb|lbs|gram|grams|g)\b", text, flags=re.IGNORECASE))


def _is_weak_instruction_set(instructions: list) -> bool:
    texts = [instruction.text for instruction in instructions]
    return len(texts) < 3 or any(len(text.split()) < 4 for text in texts)


def _expand_generic_steps(instructions: list) -> list:
    texts = [instruction.text for instruction in instructions]
    if len(texts) >= 3:
        return instructions
    return _instruction_set(
        [
            "Prepare the ingredients according to the recipe notes.",
            "Cook the main ingredients using the stated method until properly done.",
            "Season to taste and serve while fresh.",
        ]
    )


def _instruction_set(texts: list[str]) -> list:
    from app.schemas import RecipeInstructionDraft

    return [RecipeInstructionDraft(step=index, text=text) for index, text in enumerate(texts, start=1)]
