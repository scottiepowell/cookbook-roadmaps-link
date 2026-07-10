import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai_access_models import AiAccessWorkflow
from app.ai_invite_sessions import invite_router, require_demo_workflow_access
from app.ai_operator_gate import check_operator_gate
from app.config import get_ai_settings, get_invite_session_settings, get_operator_gate_settings, get_provider_config, get_recipe_dataset_dir
from app.dataset_rag import DatasetAskProviderError, ask_dataset_recipes
from app.dataset_retrieval import search_dataset_recipes
from app.importer import RecipeImportProviderError, RecipeImportValidationError, import_recipe_text
from app.meal_plan_endpoint import MealPlanProviderError, MealPlanValidationError, create_meal_plan
from app.observability import configure_logging, log_ai_workflow, request_logging_middleware
from app.providers.errors import extract_provider_debug_details
from app.recipe_reader import NoRecipeTableFoundError, RecipeReaderError, load_recipe_documents
from app.recipe_session_routes import router as recipe_session_router
from app.rag import AskProviderError, ask_cookbook
from app.schemas import (
    AskRequest,
    AskResponse,
    ConfigResponse,
    DatasetAskRequest,
    DatasetAskResponse,
    DatasetSearchRequest,
    DatasetSearchResponse,
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
configure_logging()
app.middleware("http")(request_logging_middleware)
app.include_router(recipe_session_router)
app.include_router(invite_router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/demo", include_in_schema=False)
@app.get("/demo/ai", include_in_schema=False)
def ai_demo() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo.html", media_type="text/html")


@app.get("/demo/readiness", include_in_schema=False)
def demo_readiness() -> dict[str, object]:
    settings = get_ai_settings()
    invite_settings = get_invite_session_settings()
    recipe_count = _safe_recipe_count()
    dataset_available = Path(get_recipe_dataset_dir()).exists()

    return {
        "service": {"ok": True, "name": "ai-api"},
        "provider": {
            "mode": settings.provider,
            "model": settings.openai_model if settings.provider == "openai" else settings.model,
            "offline_demo_mode": settings.provider == "mock",
        },
        "saved_recipes": {
            "available": recipe_count is not None and recipe_count > 0,
            "count": recipe_count or 0,
            "message": (
                "Saved recipes are available for Ask My Cookbook and meal planning."
                if recipe_count
                else "Saved-recipe data is not available; importer and dataset workflows can still be demoed."
            ),
        },
        "dataset": {
            "available": dataset_available,
            "message": (
                "Local dataset data is configured for dataset search and dataset ask."
                if dataset_available
                else "Local dataset data is not available; saved-recipe and importer workflows can still be demoed."
            ),
        },
        "invite_sessions": {
            "available": invite_settings.enabled and invite_settings.configured,
            "message": (
                "Invite-only demo sessions are enabled for local/private use."
                if invite_settings.enabled and invite_settings.configured
                else "Invite-only demo sessions are disabled by default."
                if not invite_settings.enabled
                else "Invite-only demo sessions are enabled, but the configuration needs attention."
            ),
            "allowed_workflows": list(invite_settings.allowed_workflows),
            "local_operator_create_enabled": invite_settings.local_operator_create_enabled,
        },
    }


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
    request: Request,
    q: str = "",
    limit: int = Query(default=10, ge=1, le=50),
) -> RecipeSearchResponse:
    response = _search_response(query=q, limit=limit)
    log_ai_workflow("recipes.search", request, retrieved_count=response.count, citation_count=0, warning_count=0)
    return response


@app.post("/recipes/search", response_model=RecipeSearchResponse)
def search_recipes_post(payload: RecipeSearchRequest, request: Request) -> RecipeSearchResponse:
    response = _search_response(query=payload.query, limit=payload.limit)
    log_ai_workflow("recipes.search", request, retrieved_count=response.count, citation_count=0, warning_count=0)
    return response


@app.get("/dataset/search", response_model=DatasetSearchResponse)
def search_dataset_get(
    request: Request,
    q: str = "",
    limit: int = Query(default=10, ge=1, le=50),
    dataset_limit: int | None = Query(default=None, ge=1, le=5000),
) -> DatasetSearchResponse:
    response = search_dataset_recipes(query=q, limit=limit, dataset_limit=dataset_limit)
    log_ai_workflow(
        "dataset.search",
        request,
        retrieved_count=response.count,
        citation_count=0,
        warning_count=len(response.warnings),
    )
    return response


@app.post("/dataset/search", response_model=DatasetSearchResponse)
def search_dataset_post(payload: DatasetSearchRequest, request: Request) -> DatasetSearchResponse:
    response = search_dataset_recipes(query=payload.query, limit=payload.limit, dataset_limit=payload.dataset_limit)
    log_ai_workflow(
        "dataset.search",
        request,
        retrieved_count=response.count,
        citation_count=0,
        warning_count=len(response.warnings),
    )
    return response


@app.post("/dataset/ask", response_model=DatasetAskResponse)
def ask_dataset(payload: DatasetAskRequest, request: Request) -> DatasetAskResponse:
    access_session = _require_demo_workflow_access(request, AiAccessWorkflow.DATASET_ASK)
    try:
        response = ask_dataset_recipes(payload, session_state=access_session)
        log_ai_workflow(
            "dataset.ask",
            request,
            provider=response.provider,
            model=response.model,
            retrieved_count=response.retrieval.retrieved_count,
            citation_count=len(response.citations),
            warning_count=len(response.warnings),
        )
        return response
    except DatasetAskProviderError as exc:
        log_ai_workflow(
            "dataset.ask",
            request,
            status="error",
            safe_error_type=exc.__class__.__name__,
            **_provider_debug_log_fields(exc),
        )
        raise HTTPException(status_code=503, detail="Dataset ask provider is not available.") from exc


@app.post("/ai/import-recipe", response_model=RecipeImportResponse)
def import_recipe(payload: RecipeImportRequest, request: Request) -> RecipeImportResponse:
    access_session = _require_demo_workflow_access(request, AiAccessWorkflow.IMPORTER)
    try:
        response = import_recipe_text(payload, session_state=access_session)
        log_ai_workflow(
            "recipe.import",
            request,
            provider=response.provider,
            model=response.model,
            retrieved_count=response.retrieval.retrieved_count if response.retrieval else 0,
            citation_count=len(response.citations),
            warning_count=len(response.warnings),
        )
        return response
    except RecipeImportProviderError as exc:
        log_ai_workflow(
            "recipe.import",
            request,
            status="error",
            safe_error_type=exc.__class__.__name__,
            **_provider_debug_log_fields(exc),
        )
        raise HTTPException(status_code=503, detail="Recipe importer provider is not available.") from exc
    except RecipeImportValidationError as exc:
        log_ai_workflow("recipe.import", request, status="error", safe_error_type=exc.__class__.__name__)
        raise HTTPException(status_code=502, detail="Recipe importer returned an invalid draft.") from exc


@app.post("/ai/ask", response_model=AskResponse)
def ask_my_cookbook(payload: AskRequest, request: Request) -> AskResponse:
    try:
        response = ask_cookbook(payload)
        log_ai_workflow(
            "cookbook.ask",
            request,
            provider=response.provider,
            model=response.model,
            retrieved_count=response.retrieval.retrieved_count,
            citation_count=len(response.citations),
            warning_count=len(response.warnings),
        )
        return response
    except NoRecipeTableFoundError as exc:
        log_ai_workflow("cookbook.ask", request, status="error", safe_error_type=exc.__class__.__name__)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RecipeReaderError as exc:
        log_ai_workflow("cookbook.ask", request, status="error", safe_error_type=exc.__class__.__name__)
        raise HTTPException(status_code=500, detail="Recipe database could not be read.") from exc
    except AskProviderError as exc:
        log_ai_workflow(
            "cookbook.ask",
            request,
            status="error",
            safe_error_type=exc.__class__.__name__,
            **_provider_debug_log_fields(exc),
        )
        raise HTTPException(status_code=503, detail="Ask provider is not available.") from exc


@app.post("/ai/meal-plan", response_model=MealPlanResponse)
def meal_plan(payload: MealPlanRequest, request: Request) -> MealPlanResponse:
    access_session = _require_demo_workflow_access(request, AiAccessWorkflow.MEAL_PLAN)
    try:
        response = create_meal_plan(payload, session_state=access_session)
        log_ai_workflow(
            "meal.plan",
            request,
            provider=response.provider,
            model=response.model,
            retrieved_count=response.selection.candidate_count,
            citation_count=len(response.citations),
            warning_count=len(response.warnings),
        )
        return response
    except NoRecipeTableFoundError as exc:
        log_ai_workflow("meal.plan", request, status="error", safe_error_type=exc.__class__.__name__)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RecipeReaderError as exc:
        log_ai_workflow("meal.plan", request, status="error", safe_error_type=exc.__class__.__name__)
        raise HTTPException(status_code=500, detail="Recipe database could not be read.") from exc
    except MealPlanProviderError as exc:
        log_ai_workflow(
            "meal.plan",
            request,
            status="error",
            safe_error_type=exc.__class__.__name__,
            **_provider_debug_log_fields(exc),
        )
        raise HTTPException(status_code=503, detail="Meal-plan provider is not available.") from exc
    except MealPlanValidationError as exc:
        log_ai_workflow("meal.plan", request, status="error", safe_error_type=exc.__class__.__name__)
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


def _safe_recipe_count() -> int | None:
    try:
        return len(load_recipe_documents())
    except (NoRecipeTableFoundError, RecipeReaderError, OSError, sqlite3.Error):
        return None


def _provider_debug_log_fields(exc: BaseException) -> dict[str, str]:
    if not get_ai_settings().provider_debug:
        return {}

    details = extract_provider_debug_details(exc)
    if details is None:
        return {}

    return {
        "provider_error_category": details.category,
        "provider_error_type": details.exception_type,
        "safe_error_summary": details.safe_summary,
    }


def _require_demo_workflow_access(request: Request, workflow: AiAccessWorkflow):
    access_session = require_demo_workflow_access(
        workflow,
        request.headers,
        client_host=request.client.host if request.client else None,
    )
    if access_session is not None:
        log_ai_workflow(
            "operator.gate",
            request,
            provider="invite",
            status="allowed",
            warning_count=0,
        )
        return access_session
    decision = check_operator_gate(
        workflow,
        request.headers,
        get_operator_gate_settings(),
        client_host=request.client.host if request.client else None,
    )
    log_ai_workflow(
        "operator.gate",
        request,
        provider="operator",
        status=decision.status.value,
        warning_count=0,
    )
    return access_session
