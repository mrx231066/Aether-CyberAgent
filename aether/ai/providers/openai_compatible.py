"""OpenAI-Compatible Provider Adapter for Aether-CyberAgent.

Supports: OpenRouter, Moonshot/Kimi, Z.ai/GLM, vLLM, and any custom OpenAI-compatible API endpoint.
"""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.helpers import (
    get_cached_models, set_cached_models, parse_openai_style_models
)
from aether.engine.credentials import CredentialManager

console = Console()


class OpenAICompatibleAdapter(AetherProvider):
    """Generic adapter for any OpenAI-compatible API."""

    def __init__(self, provider_id: str, provider_name: str, base_url: str,
                 models_endpoint: Optional[str] = None):
        self.name = provider_id
        self.display_name = provider_name
        self._base_url = base_url.rstrip("/")
        self._models_endpoint = models_endpoint
        self._is_authenticated = False
        self._client = None

    def authenticate(self) -> bool:
        console.print(f"\n╭──────────────────────────────────────╮")
        console.print(f"│     [bold cyan]{self.display_name.upper():^30}[/bold cyan] │")
        console.print(f"╰──────────────────────────────────────╯")
        api_key = Prompt.ask(f"Enter {self.display_name} API Key", password=True)
        if not api_key:
            return False
        CredentialManager.save_credential(self.name, api_key)
        self._is_authenticated = True
        self._init_client()
        return True

    def _init_client(self):
        try:
            import openai
            key = CredentialManager.get_credential(self.name)
            if key:
                self._client = openai.OpenAI(api_key=key, base_url=self._base_url)
        except Exception as e:
            console.print(f"[dim yellow]{self.display_name} client initialization notice: {e}[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential(self.name) is not None

    def list_models(self, force_refresh: bool = False) -> List[ModelMetadata]:
        if not force_refresh:
            cached = get_cached_models(self.name)
            if cached:
                return cached

        self._init_client()
        if not self._client:
            raise RuntimeError(f"{self.display_name} client not authenticated or missing API Key.")

        # Attempt HTTP GET via httpx if explicit endpoint or standard client.models.list()
        try:
            raw_data = None
            if self._models_endpoint:
                import httpx
                key = CredentialManager.get_credential(self.name)
                headers = {"Authorization": f"Bearer {key}"} if key else {}
                resp = httpx.get(self._models_endpoint, headers=headers, timeout=10)
                if resp.status_code == 200:
                    raw_data = resp.json()
                else:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:100]}")

            if raw_data is None:
                raw_data = self._client.models.list()

            parsed = parse_openai_style_models(
                raw_data=raw_data,
                provider_name=self.name,
                provider_display_name=self.display_name
            )
            set_cached_models(self.name, parsed)
            return parsed
        except Exception as e:
            raise RuntimeError(f"{self.display_name} live model discovery failed: {e}")

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        try:
            for m in self.list_models():
                if m.model_id == model_id:
                    return m
        except Exception:
            pass
        return None

    def generate(self, request: str, model_id: Optional[str] = None, **kwargs) -> str:
        self._init_client()
        if not self._client:
            return f"[Error: {self.display_name} client not initialized or missing API Key]"
            
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "default"
            except Exception:
                target_model = "default"

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            messages = [
                {"role": "system", "content": AETHER_IDENTITY_PROMPT},
                {"role": "user", "content": request}
            ]
            response = self._client.chat.completions.create(
                model=target_model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[{self.display_name} Error: {e}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield f"[Error: {self.display_name} client not initialized or missing API Key]"
            return
            
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "default"
            except Exception:
                target_model = "default"

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            messages = [
                {"role": "system", "content": AETHER_IDENTITY_PROMPT},
                {"role": "user", "content": request}
            ]
            response = self._client.chat.completions.create(
                model=target_model,
                messages=messages,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[{self.display_name} Stream Error: {e}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential(self.name)
        self._is_authenticated = False
        self._client = None


# ── Pre-configured Provider Factories ──

def create_openrouter_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="openrouter",
        provider_name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        models_endpoint="https://openrouter.ai/api/v1/models",
    )

def create_moonshot_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="moonshot",
        provider_name="Moonshot AI / Kimi",
        base_url="https://api.moonshot.cn/v1",
        models_endpoint="https://api.moonshot.cn/v1/models",
    )

def create_zai_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="zai",
        provider_name="Z.ai / GLM",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        models_endpoint="https://open.bigmodel.cn/api/paas/v4/models",
    )

def create_vllm_adapter(base_url: str = "http://localhost:8000/v1") -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="vllm",
        provider_name="vLLM (Local)",
        base_url=base_url,
        models_endpoint=f"{base_url.rstrip('/')}/models",
    )

def create_custom_adapter(provider_id: str, provider_name: str, base_url: str) -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=base_url,
        models_endpoint=f"{base_url.rstrip('/')}/models",
    )
