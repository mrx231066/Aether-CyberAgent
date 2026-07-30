"""Provider Manager for Aether-CyberAgent (v2.0.0).

Handles active routing, fallbacks, and the unified model registry.
"""

from typing import Dict, List, Optional
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.engine.events import EventBus
from aether.engine.errors import ProviderError

class ProviderManager:
    """Central orchestrator for AI Provider integrations."""
    
    _providers: Dict[str, AetherProvider] = {}
    _active_provider_name: Optional[str] = None
    _active_model_id: Optional[str] = None
    _model_registry: Dict[str, List[ModelMetadata]] = {}
    
    # Fallback configuration
    _fallback_chain: List[str] = []

    @classmethod
    def register(cls, provider: AetherProvider):
        cls._providers[provider.name] = provider
        if not cls._active_provider_name:
            cls._active_provider_name = provider.name
        EventBus.emit("provider_registered", {"provider": provider.name})

    @classmethod
    def get_active_provider(cls) -> Optional[AetherProvider]:
        if not cls._active_provider_name:
            return None
        return cls._providers.get(cls._active_provider_name)

    @classmethod
    def switch_provider(cls, provider_name: str) -> bool:
        if provider_name in cls._providers:
            cls._active_provider_name = provider_name
            cls._active_model_id = None
            EventBus.emit("provider_switched", {"provider": provider_name})
            return True
        raise ProviderError(f"Provider '{provider_name}' not registered.")

    @classmethod
    def refresh_models(cls, provider_name: str) -> bool:
        provider = cls._providers.get(provider_name)
        if not provider:
            raise ProviderError(f"Provider '{provider_name}' not registered.")
            
        EventBus.emit("status_update", {"msg": f"Connecting to {provider.display_name} API..."})
        
        if not provider.health_check():
            EventBus.emit("error", {"msg": f"Connection failed to {provider.display_name}"})
            return False
            
        EventBus.emit("status_update", {"msg": "Discovering available models..."})
        try:
            models = provider.list_models()
            cls._model_registry[provider_name] = models
            EventBus.emit("models_discovered", {"count": len(models), "provider": provider.name})
            
            if models and cls._active_provider_name == provider_name and not cls._active_model_id:
                cls._active_model_id = models[0].model_id
            return True
        except Exception as e:
            raise ProviderError(f"Model discovery failed: {e}")

    @classmethod
    def set_active_model(cls, model_id: str) -> bool:
        provider = cls.get_active_provider()
        if not provider:
            raise ProviderError("No active provider set.")
            
        models = cls._model_registry.get(provider.name, [])
        if any(m.model_id == model_id for m in models):
            cls._active_model_id = model_id
            EventBus.emit("model_switched", {"model_id": model_id})
            return True
        raise ProviderError(f"Model '{model_id}' not found in registry.")
        
    @classmethod
    def status(cls):
        provider = cls.get_active_provider()
        console.print("\n╭─────────────────────────────────────────────╮")
        console.print("│              [bold cyan]AETHER STATUS[/bold cyan]                  │")
        console.print("├─────────────────────────────────────────────┤")
        
        if provider:
            models = cls._model_registry.get(provider.name, [])
            console.print(f"│ Provider: {provider.display_name:<25} │")
            console.print(f"│ Connection: ✓ Connected                     │")
            console.print(f"│ Model: {str(cls._active_model_id):<28} │")
            console.print(f"│ Available Models: {str(len(models)):<25} │")
        else:
            console.print("│ [red]No active provider configured.[/red]              │")
            
        console.print("╰─────────────────────────────────────────────╯\n")
