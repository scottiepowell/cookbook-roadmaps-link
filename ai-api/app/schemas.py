from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ProviderConfig(BaseModel):
    configured: bool


class ConfigResponse(BaseModel):
    providers: dict[str, ProviderConfig]
