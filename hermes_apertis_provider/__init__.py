"""Apertis AI model-provider profile for Hermes Agent."""

from providers import register_provider
from providers.base import ProviderProfile


__version__ = "1.1.0"

apertis = ProviderProfile(
    name="apertis",
    api_mode="chat_completions",
    aliases=("apertis-ai", "apertis-api"),
    display_name="Apertis AI",
    description="Apertis AI — unified multi-model inference",
    signup_url="https://api.apertis.ai/",
    env_vars=("APERTIS_API_KEY", "APERTIS_BASE_URL"),
    base_url="https://api.apertis.ai/v1",
    auth_type="api_key",
    default_aux_model="gpt-5.4-mini",
    fallback_models=(
        "gpt-5.6-sol",
        "gpt-5.5",
        "gpt-5.4-mini",
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "gemini-3.1-pro-preview",
    ),
)


def register() -> None:
    """Register the Apertis profile with the host Hermes process."""
    register_provider(apertis)


__all__ = ("__version__", "apertis", "register")
