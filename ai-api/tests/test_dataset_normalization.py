from app.dataset_adapter import ExternalRecipeRecord
from app.dataset_index import build_recipe_index, search_recipe_index
from app.dataset_normalization import extract_phrases, normalize_index_text, normalize_text, safe_tokenize


def test_text_normalization_handles_aliases_quotes_dashes_and_accents():
    text = "Omelette with Parmigiano-Reggiano, no-bake graham crackers, and jalape\u00f1o"

    normalized = normalize_text(text)
    tokens = safe_tokenize(text)

    assert normalized == "omelet with parmesan no bake graham cracker and jalapeno"
    assert tokens == ["omelet", "with", "parmesan", "no", "bake", "graham", "cracker", "and", "jalapeno"]


def test_phrase_extraction_preserves_important_recipe_terms():
    text = "Classic baked cheesecake with cream cheese, graham crackers, black pepper, and cream of chicken soup"

    phrases = extract_phrases(text)

    assert "baked cheesecake" in phrases
    assert "cream cheese" in phrases
    assert "graham cracker" in phrases
    assert "cream of chicken" in phrases
    assert "cream of chicken soup" in phrases
    assert "black pepper" in phrases


def test_normalized_index_text_records_aliases_and_singulars():
    normalized = normalize_index_text("No-Bake Cheesecake Bars with graham crackers and eggs")

    assert normalized.normalized == "no bake cheesecake bars with graham cracker and eggs"
    assert "graham cracker" in normalized.phrases
    assert "no-bake" in normalized.aliases_applied
    assert "graham crackers" in normalized.aliases_applied
    assert normalized.tokens == ["no", "bake", "cheesecake", "bar", "with", "graham", "cracker", "and", "egg"]


def test_normalized_index_scoring_prefers_phrase_matches_over_generic_records():
    index = build_recipe_index(
        [
            ExternalRecipeRecord(
                source_id="nobake-1",
                title="No-Bake Cheesecake Bars",
                ingredients=["cream cheese", "sugar", "whipped cream", "graham crackers", "vanilla"],
                instructions=["Press crust into pan", "Mix filling", "Chill until set"],
                tags=["dessert"],
                source_file="13k-recipes.csv",
            ),
            ExternalRecipeRecord(
                source_id="frosting-1",
                title="Cream Cheese Frosting",
                ingredients=["cream cheese", "butter", "sugar", "vanilla"],
                instructions=["Beat cream cheese and butter", "Add sugar", "Mix until fluffy"],
                tags=["dessert"],
                source_file="13k-recipes.csv",
            ),
        ]
    )

    results = search_recipe_index(index, "no-bake cheesecake with graham crackers chill", limit=5)

    assert [result.source_id for result in results] == ["nobake-1", "frosting-1"]
    assert results[0].score > results[1].score
    assert results[0].title == "No-Bake Cheesecake Bars"
    assert results[0].matched_fields[0] == "title"


def test_normalized_index_preserves_original_display_values_and_avoids_secret_like_metadata():
    index = build_recipe_index(
        [
            ExternalRecipeRecord(
                source_id="omelet-1",
                title="Cheese Omelet",
                ingredients=["eggs", "cheese", "butter"],
                instructions=["Beat the eggs", "Cook in butter", "Fold and serve"],
                tags=["breakfast"],
                source_file="13k-recipes.csv",
            )
        ]
    )

    document = index.documents[0]

    assert document.document.title == "Cheese Omelet"
    assert document.document.ingredients == ["eggs", "cheese", "butter"]
    assert document.normalized_fields["title"] == "cheese omelet"
    assert document.normalized_fields["source"] == "13k recipes csv"
    assert "C:\\" not in document.normalized_fields["source"]
    assert "sk-" not in document.normalized_fields["source"]
    assert all("C:\\" not in phrase for phrase in document.normalized_field_phrases["title"])
