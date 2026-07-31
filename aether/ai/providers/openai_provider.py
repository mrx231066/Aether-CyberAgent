"""OpenAI Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.engine.credentials import CredentialManager

console = Console()


class OpenAIAdapter(AetherProvider):

    name = "openai"
    display_name = "OpenAI"

    def __init__(self):
        self._is_authenticated = False
        self._client = None

    def authenticate(self) -> bool:
        console.print("\n╭──────────────────────────────────────╮")
        console.print("│       [bold green]OPENAI SETUP[/bold green]                  │")
        console.print("╰──────────────────────────────────────╯")
        api_key = Prompt.ask("Enter OpenAI API Key", password=True)
        if not api_key:
            return False
        CredentialManager.save_credential("openai", api_key)
        self._is_authenticated = True
        self._init_client()
        return True

    def _init_client(self):
        try:
            import openai
            key = CredentialManager.get_credential("openai")
            if key:
                self._client = openai.OpenAI(api_key=key)
        except ImportError:
            console.print("[dim yellow]openai package not installed. Install with: pip install openai[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential("openai") is not None

    def list_models(self) -> List[ModelMetadata]:
        self._init_client()
        if self._client:
            try:
                models = self._client.models.list()
                result = []
                for m in models.data:
                    if "gpt" in m.id or "o1" in m.id or "o3" in m.id:
                        result.append(ModelMetadata(
                            provider=self.name,
                            provider_display_name=self.display_name,
                            model_id=m.id,
                            display_name=m.id,
                            capabilities={"streaming": True, "vision": "vision" in m.id or "4o" in m.id, "tools": True},
                        ))
                return sorted(result, key=lambda x: x.model_id)
            except Exception:
                pass
        # Fallback static list
        return [
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="gpt-4o", display_name="GPT-4o", capabilities={"streaming": True, "vision": True, "tools": True}),
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="gpt-4o-mini", display_name="GPT-4o Mini", capabilities={"streaming": True, "vision": True, "tools": True}),
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="o3-mini", display_name="o3-mini", capabilities={"streaming": True, "vision": False, "tools": True}),
        ]

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    def generate(self, request: str, model_id: str, **kwargs) -> str:
        self._init_client()
        if not self._client:
            return "[Error: OpenAI client not initialized]"
        try:
            response = self._client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": request}],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Error: {e}]"

    def stream(self, request: str, model_id: str, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield "[Error: OpenAI client not initialized]"
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
            yield f"[OpenAI Stream Error: {e}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("openai")
        self._is_authenticated = False
        self._client = None
