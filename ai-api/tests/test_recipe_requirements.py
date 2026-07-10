from __future__ import annotations

from datetime import UTC, datetime

from app.recipe_requirements import (
    RecipeFollowUpLabel,
    RecipeClarificationQuestion,
    RecipeRequirementConfidence,
    RecipeRequirementField,
    RecipeRequirementSource,
    RecipeRequirementsState,
    classify_follow_up,
    decide_clarification,
    decide_rag_refresh,
    extract_recipe_requirements,
)


def values(fields):
    return [field.value for field in fields]


def test_extracts_cheesecake_requirements():
    state = extract_recipe_requirements(
        "classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight",
        now=datetime(2026, 7, 10, tzinfo=UTC),
    )

    assert state.dish_intent.value == "cheesecake"
    assert state.serving_count.value == 4
    assert state.serving_count.source == RecipeRequirementSource.USER_PROVIDED
    assert "cream cheese" in values(state.required_ingredients)
    assert "graham cracker crust" in values(state.required_ingredients)
    assert "egg" in values(state.required_ingredients)
    assert state.cooking_method
    assert "baked" in state.cooking_method.value
    assert "chill" in state.cooking_method.value
    assert "overnight" in values(state.time_constraints)
    assert "classic" in values(state.texture_or_style_goals)
    assert state.confidence_label == RecipeRequirementConfidence.HIGH


def test_extracts_carbonara_requirements_and_exclusion():
    state = extract_recipe_requirements(
        "carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream"
    )

    assert state.dish_intent.value == "carbonara"
    assert state.serving_count.value == 4
    assert "spaghetti" in values(state.required_ingredients)
    assert "egg" in values(state.required_ingredients)
    assert "parmesan" in values(state.required_ingredients)
    assert "pancetta" in values(state.required_ingredients)
    assert "black pepper" in values(state.required_ingredients)
    assert "heavy cream" in values(state.excluded_ingredients)
    assert "heavy cream" not in values(state.required_ingredients)
    assert state.confidence_label == RecipeRequirementConfidence.HIGH


def test_extracts_omelet_alias_and_equipment():
    state = extract_recipe_requirements("omelette for 4 with eggs cheddar onions butter folded in a skillet")

    assert state.dish_intent.value == "omelet"
    assert state.serving_count.value == 4
    assert "egg" in values(state.required_ingredients)
    assert "cheddar" in values(state.required_ingredients)
    assert "onion" in values(state.required_ingredients)
    assert "skillet" in state.cooking_method.value
    assert "skillet" in values(state.equipment_constraints)
    assert state.confidence_label == RecipeRequirementConfidence.HIGH


def test_extracts_chicken_rice_casserole_requirements():
    state = extract_recipe_requirements(
        "chicken and rice casserole for 6 with cooked chicken rice cream of chicken soup cheddar bake until bubbly"
    )

    assert state.dish_intent.value == "chicken and rice casserole"
    assert state.serving_count.value == 6
    assert "chicken" in values(state.required_ingredients)
    assert "rice" in values(state.required_ingredients)
    assert "cream of chicken soup" in values(state.required_ingredients)
    assert "cheddar" in values(state.required_ingredients)
    assert state.cooking_method.value == "baked"
    assert state.confidence_label == RecipeRequirementConfidence.HIGH


def test_extracts_no_bake_method_and_dietary_constraint():
    state = extract_recipe_requirements(
        "no-bake cheesecake for 4 with cream cheese vanilla sugar graham cracker crust chill until firm gluten-free"
    )

    assert state.dish_intent.value == "cheesecake"
    assert state.cooking_method
    assert "no-bake" in state.cooking_method.value
    assert "chill" in state.cooking_method.value
    assert "gluten free" in values(state.dietary_constraints)


def test_default_servings_and_requirement_sources():
    state = extract_recipe_requirements("cheesecake with cream cheese sugar eggs vanilla graham cracker crust bake and chill")

    assert state.serving_count.value == 4
    assert state.serving_count.source == RecipeRequirementSource.DEFAULTED
    assert "serving_count" in state.requirement_sources["defaulted"]
    assert "Default servings are 4 when not specified." in values(state.assumptions)


def test_confidence_low_and_rejected():
    vague = extract_recipe_requirements("make dessert")
    rejected = extract_recipe_requirements("!!!!!")

    assert vague.confidence_label == RecipeRequirementConfidence.LOW
    assert rejected.confidence_label == RecipeRequirementConfidence.REJECTED


def test_clarification_needed_for_vague_dessert():
    state = extract_recipe_requirements("make dessert")
    decision = decide_clarification(state)

    assert decision.should_clarify is True
    assert decision.question
    assert "dish" in decision.question.lower()
    assert decision.confidence_label == RecipeRequirementConfidence.LOW


def test_no_clarification_for_detailed_cheesecake_notes():
    state = extract_recipe_requirements(
        "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill"
    )
    decision = decide_clarification(state)

    assert decision.should_clarify is False
    assert decision.question is None


def test_chicken_casserole_safety_clarification_when_handling_unknown():
    state = extract_recipe_requirements("chicken rice casserole bake until hot")
    decision = decide_clarification(state)

    assert decision.should_clarify is True
    assert "chicken" in decision.question.lower()
    assert "cooked" in decision.question.lower()


def test_follow_up_delta_classification_examples():
    current = extract_recipe_requirements("classic baked cheesecake for 4 with cream cheese graham cracker crust")
    current.open_questions.append(RecipeClarificationQuestion(id="q1", question="Baked or no-bake?", reason="method ambiguity"))

    assert classify_follow_up("actually make it no-bake").label == RecipeFollowUpLabel.RELEVANT_REQUIREMENT_UPDATE
    assert classify_follow_up("use ricotta instead of cream cheese").label == RecipeFollowUpLabel.CORRECTION_TO_ASSUMPTION
    assert classify_follow_up("make it gluten-free").label == RecipeFollowUpLabel.RELEVANT_REQUIREMENT_UPDATE
    assert classify_follow_up("I only have an air fryer").label == RecipeFollowUpLabel.RELEVANT_REQUIREMENT_UPDATE
    assert classify_follow_up("thanks").label == RecipeFollowUpLabel.IRRELEVANT_CHATTER
    assert classify_follow_up("make it shorter").label == RecipeFollowUpLabel.FORMATTING_ONLY
    assert classify_follow_up("regenerate it").label == RecipeFollowUpLabel.REGENERATE_WITHOUT_NEW_REQUIREMENTS
    assert classify_follow_up("save this").label == RecipeFollowUpLabel.SAVE_OR_FINALIZE_REQUEST


def test_clarification_answer_when_question_open():
    state = extract_recipe_requirements("make dessert")
    state.open_questions.append(RecipeClarificationQuestion(id="q1", question="What dessert?", reason="vague"))

    result = classify_follow_up("cheesecake", current_state=state)

    assert result.label == RecipeFollowUpLabel.CLARIFICATION_ANSWER
    assert result.should_refresh_rag is True
    assert result.provider_generation_likely_needed is True


def test_rag_refresh_true_for_material_method_change():
    previous = extract_recipe_requirements("classic baked cheesecake for 4 with cream cheese graham cracker crust")
    current = extract_recipe_requirements("classic no-bake cheesecake for 4 with cream cheese graham cracker crust chill")
    follow_up = classify_follow_up("actually make it no-bake")

    decision = decide_rag_refresh(previous, current, follow_up=follow_up)

    assert decision.should_refresh_rag is True
    assert "cooking_method" in decision.changed_fields
    assert "changed" in decision.reason


def test_rag_refresh_false_for_chatter_formatting_and_finalize():
    previous = extract_recipe_requirements("cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill")
    current = previous.model_copy(deep=True)

    for text in ("thanks", "looks good", "make it shorter", "save this"):
        decision = decide_rag_refresh(previous, current, follow_up=classify_follow_up(text))
        assert decision.should_refresh_rag is False


def test_safe_serialization_excludes_runtime_secret_fields():
    state = extract_recipe_requirements("cheesecake with cream cheese sugar eggs vanilla graham cracker crust bake and chill")
    dumped = str(state.model_dump())

    assert "raw_provider" not in dumped
    assert "OPENAI_API_KEY" not in dumped
    assert ".env" not in dumped
    assert "C:\\Users" not in dumped
    assert "Authorization" not in dumped
    assert "long_term" not in dumped
