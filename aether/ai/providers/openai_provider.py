"""OpenAI Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.helpers import (
    get_cached_models, set_cached_models, parse_openai_style_models
)
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
        except Exception as e:
            console.print(f"[dim yellow]OpenAI client initialization notice: {e}[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential("openai") is not None

    def list_models(self, force_refresh: bool = False) -> List[ModelMetadata]:
        if not force_refresh:
            cached = get_cached_models(self.name)
            if cached:
                return cached

        self._init_client()
        if not self._client:
            raise RuntimeError("OpenAI client not authenticated or missing API Key.")

        try:
            models_response = self._client.models.list()
            parsed = parse_openai_style_models(
                raw_data=models_response,
                provider_name=self.name,
                provider_display_name=self.display_name,
                filter_func=lambda m_id: any(k in m_id for k in ["gpt", "o1", "o3"])
            )
            set_cached_models(self.name, parsed)
            return parsed
        except Exception as e:
            raise RuntimeError(f"OpenAI live model discovery failed: {e}")

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
            return "[Error: OpenAI client not initialized or missing API Key]"
        
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "gpt-4o"
            except Exception:
                target_model = "gpt-4o"

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
            return f"[OpenAI Error: {e}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield "[Error: OpenAI client not initialized or missing API Key]"
            return
            
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "gpt-4o"
            except Exception:
                target_model = "gpt-4o"

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
            yield f"[OpenAI Stream Error: {e}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("openai")
        self._is_authenticated = False
        self._client = None
