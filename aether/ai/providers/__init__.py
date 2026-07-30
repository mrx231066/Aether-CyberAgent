"""Unified AI Provider Interface for Aether-CyberAgent v4.0.0"""
from typing import Protocol, Dict, Any, Optional

class AIProvider(Protocol):
    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        ...

class ProviderManager:
    _providers: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, provider_class):
        cls._providers[name] = provider_class
        
    @classmethod
    def get_provider(cls, name: str, **kwargs):
        provider_cls = cls._providers.get(name)
        if provider_cls:
            return provider_cls(**kwargs)
        raise ValueError(f"Provider {name} not found.")
