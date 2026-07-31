"""Shared model discovery parsing helpers and session cache for Aether providers."""

from typing import List, Dict, Any, Optional, Callable
from aether.ai.providers.base import ModelMetadata

# In-memory per-session model cache: provider_name -> List[ModelMetadata]
_SESSION_MODEL_CACHE: Dict[str, List[ModelMetadata]] = {}

def get_cached_models(provider_name: str) -> Optional[List[ModelMetadata]]:
    """Retrieve cached models for a provider for the current session."""
    return _SESSION_MODEL_CACHE.get(provider_name)

def set_cached_models(provider_name: str, models: List[ModelMetadata]) -> None:
    """Cache fetched models for a provider for the current session."""
    _SESSION_MODEL_CACHE[provider_name] = models

def clear_model_cache(provider_name: Optional[str] = None) -> None:
    """Clear session model cache for a specific provider or all providers."""
    if provider_name:
        _SESSION_MODEL_CACHE.pop(provider_name, None)
    else:
        _SESSION_MODEL_CACHE.clear()

def parse_openai_style_models(
    raw_data: Any,
    provider_name: str,
    provider_display_name: str,
    filter_func: Optional[Callable[[str], bool]] = None
) -> List[ModelMetadata]:
    """Parse OpenAI-style model discovery response (e.g. {"data": [{"id": ...}]}).
    
    Reused across OpenAI, Moonshot/Kimi, Z.ai/GLM, OpenRouter, and custom OpenAI-compatible endpoints.
    """
    items = []
    if isinstance(raw_data, dict) and "data" in raw_data:
        items = raw_data["data"]
    elif isinstance(raw_data, list):
        items = raw_data
    elif hasattr(raw_data, "data"):
        items = getattr(raw_data, "data")
    else:
        items = raw_data

    result = []
    for item in items:
        if isinstance(item, dict):
            m_id = item.get("id") or item.get("name") or ""
            disp = item.get("name") or item.get("display_name") or m_id
            ctx = item.get("context_length", 0) or item.get("context_window", 0)
        else:
            m_id = getattr(item, "id", "") or getattr(item, "name", "")
            disp = getattr(item, "name", m_id) or m_id
            ctx = getattr(item, "context_length", 0)

        if not m_id:
            continue

        if filter_func and not filter_func(m_id):
            continue

        result.append(ModelMetadata(
            provider=provider_name,
            provider_display_name=provider_display_name,
            model_id=m_id,
            display_name=disp,
            capabilities={
                "streaming": True,
                "vision": any(v in m_id.lower() for v in ["vision", "4o", "glm-4v", "claude-3"]),
                "tools": True
            },
            context_length=ctx
        ))

    if not result:
        raise ValueError(f"No valid models found in {provider_display_name} API response.")

    return sorted(result, key=lambda x: x.model_id)
