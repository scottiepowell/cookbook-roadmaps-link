from fastapi import FastAPI

from app.config import get_provider_config
from app.schemas import ConfigResponse, HealthResponse, ProviderConfig

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
