"""Anthropic Claude Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.helpers import get_cached_models, set_cached_models
from aether.engine.credentials import CredentialManager

console = Console()


class AnthropicAdapter(AetherProvider):

    name = "anthropic"
    display_name = "Anthropic Claude"

    def __init__(self):
        self._is_authenticated = False
        self._client = None

    def authenticate(self) -> bool:
        console.print("\n╭──────────────────────────────────────╮")
        console.print("│     [bold magenta]ANTHROPIC CLAUDE SETUP[/bold magenta]           │")
        console.print("╰──────────────────────────────────────╯")
        api_key = Prompt.ask("Enter Anthropic API Key", password=True)
        if not api_key:
            return False
        CredentialManager.save_credential("anthropic", api_key)
        self._is_authenticated = True
        self._init_client()
        return True

    def _init_client(self):
        try:
            import anthropic
            key = CredentialManager.get_credential("anthropic")
            if key:
                self._client = anthropic.Anthropic(api_key=key)
        except Exception as e:
            console.print(f"[dim yellow]Anthropic client initialization notice: {e}[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential("anthropic") is not None

    def list_models(self, force_refresh: bool = False) -> List[ModelMetadata]:
        if not force_refresh:
            cached = get_cached_models(self.name)
            if cached:
                return cached

        self._init_client()
        if not self._client:
            raise RuntimeError("Anthropic client not authenticated or missing API Key.")

        try:
            # Live dynamic model listing call via Anthropic SDK
            response = self._client.models.list()
            models_data = getattr(response, "data", response)
            result = []
            for item in models_data:
                m_id = getattr(item, "id", "") or item.get("id", "")
                disp = getattr(item, "display_name", m_id) or item.get("display_name", m_id) or m_id
                if not m_id:
                    continue
                result.append(ModelMetadata(
                    provider=self.name,
                    provider_display_name=self.display_name,
                    model_id=m_id,
                    display_name=disp,
                    capabilities={"streaming": True, "vision": True, "tools": True},
                    context_length=200000
                ))

            if not result:
                raise ValueError("No models returned by Anthropic API.")

            sorted_result = sorted(result, key=lambda x: x.model_id)
            set_cached_models(self.name, sorted_result)
            return sorted_result
        except Exception as e:
            raise RuntimeError(f"Anthropic live model discovery failed: {e}")

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
            return "[Error: Anthropic client not initialized or missing API Key]"
        
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "claude-3-5-sonnet-20241022"
            except Exception:
                target_model = "claude-3-5-sonnet-20241022"

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            message = self._client.messages.create(
                model=target_model,
                max_tokens=4096,
                system=AETHER_IDENTITY_PROMPT,
                messages=[{"role": "user", "content": request}],
            )
            return message.content[0].text
        except Exception as e:
            return f"[Anthropic Error: {e}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield "[Error: Anthropic client not initialized or missing API Key]"
            return
            
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "claude-3-5-sonnet-20241022"
            except Exception:
                target_model = "claude-3-5-sonnet-20241022"

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            with self._client.messages.stream(
                model=target_model,
                max_tokens=4096,
                system=AETHER_IDENTITY_PROMPT,
                messages=[{"role": "user", "content": request}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Anthropic Stream Error: {e}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("anthropic")
        self._is_authenticated = False
        self._client = None
