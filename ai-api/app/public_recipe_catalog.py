"""Reviewed link catalog: metadata only, no scraped recipe text or live crawler."""
from fastapi import APIRouter, Request
from app.ai_access_models import AiAccessWorkflow
from app.ai_invite_sessions import require_demo_workflow_access

CATALOG = [
    {"uid": "foodnetwork-spring-vegetable-salad", "name": "Spring Vegetable Salad",
     "source": "Food Network Kitchen",
     "url": "https://www.foodnetwork.com/recipes/food-network-kitchen/spring-vegetable-salad-3364967",
     "ingredients": "carrot, lettuce, red onion", "verified": "2026-09-13"},
    {"uid": "budgetbytes-carrot-soup", "name": "Carrot Soup", "source": "Budget Bytes",
     "url": "https://www.budgetbytes.com/carrot-soup/",
     "ingredients": "carrot, yellow onion, ginger, butter", "verified": "2026-09-13"},
    {"uid": "loveandlemons-carrot-salad", "name": "Carrot Salad", "source": "Love and Lemons",
     "url": "https://www.loveandlemons.com/carrot-salad-recipe/",
     "ingredients": "carrot, dates, pistachios, lemon", "verified": "2026-09-13"},
]

router = APIRouter()


@router.get("/ai/public-recipes")
def public_recipes(request: Request):
    require_demo_workflow_access(AiAccessWorkflow.RECIPE_SESSION, request.headers,
                                client_host=request.client.host if request.client else None)
    return {"recipes": CATALOG, "scope": "curated_catalog", "count": len(CATALOG)}
