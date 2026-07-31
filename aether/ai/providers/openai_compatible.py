"""OpenAI-Compatible Provider Adapter for Aether-CyberAgent.

Supports: OpenRouter, Moonshot/Kimi, Z.ai/GLM, vLLM, and any
OpenAI-compatible API endpoint.
"""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.engine.credentials import CredentialManager

console = Console()


class OpenAICompatibleAdapter(AetherProvider):
    """Generic adapter for any OpenAI-compatible API."""

    def __init__(self, provider_id: str, provider_name: str, base_url: str,
                 default_models: list = None):
        self.name = provider_id
        self.display_name = provider_name
        self._base_url = base_url
        self._default_models = default_models or []
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
        except ImportError:
            console.print("[dim yellow]openai package not installed. Install with: pip install openai[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential(self.name) is not None

    def list_models(self) -> List[ModelMetadata]:
        self._init_client()
        if self._client:
            try:
                models = self._client.models.list()
                result = []
                for m in models.data:
                    result.append(ModelMetadata(
                        provider=self.name,
                        provider_display_name=self.display_name,
                        model_id=m.id,
                        display_name=m.id,
                        capabilities={"streaming": True, "tools": True},
                    ))
                if result:
                    return sorted(result, key=lambda x: x.model_id)
            except Exception:
                pass
        # Fallback to default models
        return [
            ModelMetadata(
                provider=self.name,
                provider_display_name=self.display_name,
                model_id=m["id"],
                display_name=m["name"],
                capabilities=m.get("capabilities", {"streaming": True}),
            ) for m in self._default_models
        ]

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    def generate(self, request: str, model_id: str, **kwargs) -> str:
        self._init_client()
        if not self._client:
            return f"[Error: {self.display_name} client not initialized]"
        try:
            response = self._client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": request}],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[{self.display_name} Error: {e}]"

    def stream(self, request: str, model_id: str, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield f"[Error: {self.display_name} client not initialized]"
            return
        try:
            response = self._client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": request}],
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
        default_models=[
            {"id": "openai/gpt-4o", "name": "GPT-4o (via OpenRouter)"},
            {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4 (via OpenRouter)"},
            {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro (via OpenRouter)"},
            {"id": "meta-llama/llama-3.1-405b", "name": "Llama 3.1 405B (via OpenRouter)"},
        ],
    )

def create_moonshot_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="moonshot",
        provider_name="Moonshot AI / Kimi",
        base_url="https://api.moonshot.cn/v1",
        default_models=[
            {"id": "moonshot-v1-8k", "name": "Moonshot v1 8K"},
            {"id": "moonshot-v1-32k", "name": "Moonshot v1 32K"},
            {"id": "moonshot-v1-128k", "name": "Moonshot v1 128K"},
        ],
    )

def create_zai_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="zai",
        provider_name="Z.ai / GLM",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_models=[
            {"id": "glm-4-plus", "name": "GLM-4 Plus"},
            {"id": "glm-4-flash", "name": "GLM-4 Flash"},
            {"id": "glm-4v-plus", "name": "GLM-4V Plus (Vision)"},
        ],
    )

def create_vllm_adapter(base_url: str = "http://localhost:8000/v1") -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id="vllm",
        provider_name="vLLM (Local)",
        base_url=base_url,
        default_models=[],
    )

def create_custom_adapter(provider_id: str, provider_name: str, base_url: str) -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=base_url,
        default_models=[],
    )
