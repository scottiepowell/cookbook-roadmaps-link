class ProviderError(RuntimeError):
    """Base error for provider harness failures."""


class ProviderConfigError(ProviderError):
    """Raised for invalid or incomplete provider configuration."""


class ProviderCallError(ProviderError):
    """Raised when a provider request fails."""
