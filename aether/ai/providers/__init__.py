"""Aether Provider Registry — All built-in provider adapters."""

from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.google_gemini import GoogleGeminiAdapter
from aether.ai.providers.openai_provider import OpenAIAdapter
from aether.ai.providers.anthropic_provider import AnthropicAdapter
from aether.ai.providers.ollama_provider import OllamaAdapter
from aether.ai.providers.openai_compatible import (
    OpenAICompatibleAdapter,
    create_openrouter_adapter,
    create_moonshot_adapter,
    create_zai_adapter,
    create_vllm_adapter,
    create_custom_adapter,
)

# Provider factory map: menu_choice -> (factory_callable, needs_auth)
PROVIDER_REGISTRY = {
    "1": ("openai", lambda: OpenAIAdapter()),
    "2": ("anthropic", lambda: AnthropicAdapter()),
    "3": ("google_gemini", lambda: GoogleGeminiAdapter()),
    "4": ("moonshot", lambda: create_moonshot_adapter()),
    "5": ("zai", lambda: create_zai_adapter()),
    "6": ("openrouter", lambda: create_openrouter_adapter()),
    "7": ("ollama", lambda: OllamaAdapter()),
    "8": ("vllm", lambda: create_vllm_adapter()),
}

__all__ = [
    "AetherProvider",
    "ModelMetadata",
    "GoogleGeminiAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "OllamaAdapter",
    "OpenAICompatibleAdapter",
    "create_openrouter_adapter",
    "create_moonshot_adapter",
    "create_zai_adapter",
    "create_vllm_adapter",
    "create_custom_adapter",
    "PROVIDER_REGISTRY",
]
