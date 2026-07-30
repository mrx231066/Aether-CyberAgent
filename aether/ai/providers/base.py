"""Base Aether Provider Interface for Multi-Provider Architecture (v4.0.1)."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelMetadata:
    provider: str
    provider_display_name: str
    model_id: str
    display_name: str
    capabilities: Dict[str, bool]
    context_length: int = 0

class AetherProvider(ABC):
    """Abstract Base Class enforcing the Aether Unified Model API."""
    
    name: str = "unknown"
    display_name: str = "Unknown Provider"

    @abstractmethod
    def authenticate(self) -> bool:
        """Trigger authentication flow (OAuth or API Key)."""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate existing stored credentials."""
        pass

    @abstractmethod
    def list_models(self) -> List[ModelMetadata]:
        """Discover and normalize models from the provider API."""
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve capabilities for a specific model."""
        pass

    @abstractmethod
    def generate(self, request: str, model_id: str, **kwargs) -> str:
        """Execute a standard generation request."""
        pass

    @abstractmethod
    def stream(self, request: str, model_id: str, **kwargs) -> Any:
        """Execute a streaming generation request."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Clear credentials and terminate session."""
        pass
