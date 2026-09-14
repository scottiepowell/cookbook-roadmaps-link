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
    {"uid": "foodnetwork-carrot-red-onion-salad", "name": "Carrot and Red Onion Salad",
     "source": "Food Network / Hawa Hassan",
     "url": "https://www.foodnetwork.com/fnk/recipes/carrot-and-red-onion-salad-10034791",
     "ingredients": "carrot, red onion, cilantro, lemon", "verified": "2026-09-14"},
    {"uid": "foodnetwork-roasted-carrot-lettuce-salad",
     "name": "Roasted Carrots and Red Leaf Lettuce Salad",
     "source": "Food Network / Katie Lee Biegel",
     "url": "https://www.foodnetwork.com/recipes/katie-lee/roasted-carrots-and-red-leaf-lettuce-salad-with-buttermilk-herb-dressing-3319689",
     "ingredients": "carrot, red leaf lettuce, buttermilk, yogurt, pistachios",
     "verified": "2026-09-14"},
    {"uid": "budgetbytes-mediterranean-lentil-soup", "name": "Mediterranean Lentil Soup",
     "source": "Budget Bytes",
     "url": "https://www.budgetbytes.com/mediterranean-lentil-soup/",
     "ingredients": "lentils, yellow onion, carrot, celery, garlic, kale, lemon",
     "verified": "2026-09-14"},
    {"uid": "loveandlemons-greek-salad", "name": "Greek Salad",
     "source": "Love and Lemons",
     "url": "https://www.loveandlemons.com/greek-salad-/",
     "ingredients": "cucumber, tomato, green bell pepper, red onion, feta, olives",
     "verified": "2026-09-14"},
    {"uid": "loveandlemons-cucumber-tomato-salad", "name": "Cucumber Tomato Salad",
     "source": "Love and Lemons",
     "url": "https://www.loveandlemons.com/cucumber-tomato-salad/",
     "ingredients": "cucumber, tomato, red onion, lemon", "verified": "2026-09-14"},
]

router = APIRouter()


@router.get("/ai/public-recipes")
def public_recipes(request: Request):
    require_demo_workflow_access(AiAccessWorkflow.RECIPE_SESSION, request.headers,
                                client_host=request.client.host if request.client else None)
    return {"recipes": CATALOG, "scope": "curated_catalog", "count": len(CATALOG)}
