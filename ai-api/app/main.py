from fastapi import FastAPI, HTTPException, Query

from app.config import get_provider_config
from app.importer import RecipeImportProviderError, RecipeImportValidationError, import_recipe_text
from app.meal_plan_endpoint import MealPlanProviderError, MealPlanValidationError, create_meal_plan
from app.recipe_reader import NoRecipeTableFoundError, RecipeReaderError, load_recipe_documents
from app.rag import AskProviderError, ask_cookbook
from app.schemas import (
    AskRequest,
    AskResponse,
    ConfigResponse,
    HealthResponse,
    MealPlanRequest,
    MealPlanResponse,
    ProviderConfig,
    RecipeImportRequest,
    RecipeImportResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
)
from app.search import search_recipes

app = FastAPI(title="Cookbook AI API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-api")


@app.get("/ai/config", response_model=ConfigResponse)
def ai_config() -> ConfigResponse:
    providers = {
        name: ProviderConfig(configured=availability.configured)
        for name, availability in get_provider_config().items()
    }
    return ConfigResponse(providers=providers)


@app.get("/recipes/search", response_model=RecipeSearchResponse)
def search_recipes_get(
    q: str = "",
    limit: int = Query(default=10, ge=1, le=50),
) -> RecipeSearchResponse:
    return _search_response(query=q, limit=limit)


@app.post("/recipes/search", response_model=RecipeSearchResponse)
def search_recipes_post(request: RecipeSearchRequest) -> RecipeSearchResponse:
    return _search_response(query=request.query, limit=request.limit)


@app.post("/ai/import-recipe", response_model=RecipeImportResponse)
def import_recipe(request: RecipeImportRequest) -> RecipeImportResponse:
    try:
        return import_recipe_text(request)
    except RecipeImportProviderError as exc:
        raise HTTPException(status_code=503, detail="Recipe importer provider is not available.") from exc
    except RecipeImportValidationError as exc:
        raise HTTPException(status_code=502, detail="Recipe importer returned an invalid draft.") from exc


@app.post("/ai/ask", response_model=AskResponse)
def ask_my_cookbook(request: AskRequest) -> AskResponse:
    try:
        return ask_cookbook(request)
    except NoRecipeTableFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RecipeReaderError as exc:
        raise HTTPException(status_code=500, detail="Recipe database could not be read.") from exc
    except AskProviderError as exc:
        raise HTTPException(status_code=503, detail="Ask provider is not available.") from exc


@app.post("/ai/meal-plan", response_model=MealPlanResponse)
def meal_plan(request: MealPlanRequest) -> MealPlanResponse:
    try:
        return create_meal_plan(request)
    except NoRecipeTableFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RecipeReaderError as exc:
        raise HTTPException(status_code=500, detail="Recipe database could not be read.") from exc
    except MealPlanProviderError as exc:
        raise HTTPException(status_code=503, detail="Meal-plan provider is not available.") from exc
    except MealPlanValidationError as exc:
        raise HTTPException(status_code=502, detail="Meal-plan provider returned an invalid plan.") from exc


def _search_response(query: str, limit: int) -> RecipeSearchResponse:
    if not query.strip():
        return RecipeSearchResponse(query=query, count=0, results=[])

    try:
        recipes = load_recipe_documents()
    except NoRecipeTableFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RecipeReaderError as exc:
        raise HTTPException(status_code=500, detail="Recipe database could not be read.") from exc

    results = search_recipes(recipes, query=query, limit=limit)
    return RecipeSearchResponse(query=query, count=len(results), results=results)
