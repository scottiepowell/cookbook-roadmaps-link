from fastapi import FastAPI, HTTPException, Query

from app.config import get_provider_config
from app.recipe_reader import NoRecipeTableFoundError, RecipeReaderError, load_recipe_documents
from app.schemas import (
    ConfigResponse,
    HealthResponse,
    ProviderConfig,
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
