"""Anthropic Claude Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
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
        except ImportError:
            console.print("[dim yellow]anthropic package not installed. Install with: pip install anthropic[/dim yellow]")

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential("anthropic") is not None

    def list_models(self) -> List[ModelMetadata]:
        return [
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="claude-sonnet-4-20250514", display_name="Claude Sonnet 4", capabilities={"streaming": True, "vision": True, "tools": True}, context_length=200000),
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="claude-opus-4-20250514", display_name="Claude Opus 4", capabilities={"streaming": True, "vision": True, "tools": True}, context_length=200000),
            ModelMetadata(provider=self.name, provider_display_name=self.display_name, model_id="claude-3-5-haiku-20241022", display_name="Claude 3.5 Haiku", capabilities={"streaming": True, "vision": True, "tools": True}, context_length=200000),
        ]

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    def generate(self, request: str, model_id: str, **kwargs) -> str:
        self._init_client()
        if not self._client:
            return "[Error: Anthropic client not initialized]"
        try:
            message = self._client.messages.create(
                model=model_id,
                max_tokens=4096,
                messages=[{"role": "user", "content": request}],
            )
            return message.content[0].text
        except Exception as e:
            return f"[Anthropic Error: {e}]"

    def stream(self, request: str, model_id: str, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield "[Error: Anthropic client not initialized]"
            return
        try:
            with self._client.messages.stream(
                model=model_id,
                max_tokens=4096,
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
