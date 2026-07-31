"""Provider Manager for Aether-CyberAgent (v4.0.1).

Handles active routing, fallbacks, and the unified model registry.
"""

from typing import Dict, List, Optional
from rich.console import Console
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.engine.events import EventBus
from aether.engine.errors import ProviderError

console = Console()

class ProviderManager:
    """Central orchestrator for AI Provider integrations."""
    
    _providers: Dict[str, AetherProvider] = {}
    _active_provider_name: Optional[str] = None
    _active_model_id: Optional[str] = None
    _model_registry: Dict[str, List[ModelMetadata]] = {}
    
    # Fallback configuration
    _fallback_chain: List[str] = []

    @classmethod
    def auto_load(cls):
        """Auto-load stored credentials and restore active provider & model from user device config."""
        from aether.auth import load_config
        from aether.ai.providers import PROVIDER_REGISTRY
        from aether.engine.credentials import CredentialManager

        config = load_config()
        saved_provider = config.get("active_provider")
        saved_model = config.get("active_model")

        # Auto-instantiate any provider with stored credentials
        for choice, (p_id, factory) in PROVIDER_REGISTRY.items():
            if p_id in cls._providers:
                continue
            key = CredentialManager.get_credential(p_id)
            if key or p_id in ("ollama", "vllm"):
                try:
                    provider = factory()
                    if hasattr(provider, "_init_client"):
                        provider._init_client()
                    if provider.validate_credentials():
                        provider._is_authenticated = True
                        cls._providers[p_id] = provider
                except Exception:
                    pass

        # Select saved provider if authenticated, otherwise pick first valid provider
        if saved_provider and saved_provider in cls._providers:
            cls._active_provider_name = saved_provider
        elif cls._providers:
            cls._active_provider_name = next(iter(cls._providers))
        else:
            cls._active_provider_name = None
            cls._active_model_id = None
            return

        # Perform live model discovery on the active provider
        active_provider = cls.get_active_provider()
        if active_provider:
            try:
                models = active_provider.list_models(force_refresh=True)
                if models:
                    cls._model_registry[active_provider.name] = models
                    if saved_model and any(m.model_id == saved_model for m in models):
                        cls._active_model_id = saved_model
                    else:
                        cls._active_model_id = models[0].model_id
                else:
                    del cls._providers[active_provider.name]
                    cls._active_provider_name = None
                    cls._active_model_id = None
            except Exception:
                del cls._providers[active_provider.name]
                cls._active_provider_name = None
                cls._active_model_id = None

    @classmethod
    def register(cls, provider: AetherProvider):
        from aether.auth import save_config
        cls._providers[provider.name] = provider
        if not cls._active_provider_name:
            cls._active_provider_name = provider.name
            save_config({"active_provider": provider.name})
        EventBus.emit("provider_registered", {"provider": provider.name})

    @classmethod
    def get_active_provider(cls) -> Optional[AetherProvider]:
        if not cls._active_provider_name:
            return None
        return cls._providers.get(cls._active_provider_name)

    @classmethod
    def switch_provider(cls, provider_name: str) -> bool:
        from aether.auth import save_config
        if provider_name in cls._providers:
            cls._active_provider_name = provider_name
            cls._active_model_id = None
            save_config({"active_provider": provider_name})
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
            
        from aether.ai.providers.helpers import clear_model_cache
        clear_model_cache(provider_name)
        try:
            models = provider.list_models(force_refresh=True)
            cls._model_registry[provider_name] = models
            EventBus.emit("models_discovered", {"count": len(models), "provider": provider.name})
            
            if models and cls._active_provider_name == provider_name and not cls._active_model_id:
                cls._active_model_id = models[0].model_id
            return True
        except Exception as e:
            raise ProviderError(f"Model discovery failed: {e}")

    @classmethod
    def set_active_model(cls, model_id: str) -> bool:
        from aether.auth import save_config
        provider = cls.get_active_provider()
        if not provider:
            raise ProviderError("No active provider set.")
            
        models = cls._model_registry.get(provider.name, [])
        if any(m.model_id == model_id for m in models):
            cls._active_model_id = model_id
            save_config({"active_model": model_id})
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
