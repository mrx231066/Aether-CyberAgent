"""Google Gemini Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.engine.credentials import CredentialManager

console = Console()

class GoogleGeminiAdapter(AetherProvider):
    
    name = "google_gemini"
    display_name = "Google Gemini"
    
    def __init__(self):
        self._is_authenticated = False
        self._auth_method = "none"
        self._client = None

    def authenticate(self) -> bool:
        console.print("\n╭──────────────────────────────────────╮")
        console.print("│       [bold blue]GOOGLE GEMINI SETUP[/bold blue]            │")
        console.print("├──────────────────────────────────────┤")
        console.print("│ 1. Google Account Login (OAuth)      │")
        console.print("│ 2. Gemini API Key                    │")
        console.print("│ 3. Cancel                            │")
        console.print("╰──────────────────────────────────────╯")
        
        choice = Prompt.ask("Select authentication method", choices=["1", "2", "3"])
        
        if choice == "1":
            return self._auth_oauth()
        elif choice == "2":
            return self._auth_api_key()
        return False

    def _auth_oauth(self) -> bool:
        console.print("[dim]OAuth implementation requires valid client_secrets.json.[/dim]")
        return False

    def _auth_api_key(self) -> bool:
        api_key = Prompt.ask("Enter Gemini API Key", password=True)
        if not api_key:
            return False
        CredentialManager.save_api_key(api_key)
        self._is_authenticated = True
        self._auth_method = "api_key"
        self._init_client()
        return True

    def _init_client(self):
        try:
            from google import genai
            api_key = CredentialManager.get_api_key()
            if api_key:
                self._client = genai.Client(api_key=api_key)
        except ImportError:
            pass

    def validate_credentials(self) -> bool:
        return CredentialManager.get_api_key() is not None

    def list_models(self) -> List[ModelMetadata]:
        # Usually client.models.list() would be called here
        discovered = [
            {"name": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro"},
            {"name": "gemini-1.5-pro-latest", "display_name": "Gemini 1.5 Pro"},
            {"name": "gemini-1.5-flash-latest", "display_name": "Gemini 1.5 Flash"},
        ]
        normalized = []
        for d in discovered:
            normalized.append(ModelMetadata(
                provider=self.name,
                provider_display_name=self.display_name,
                model_id=d["name"],
                display_name=d["display_name"],
                capabilities={"streaming": True, "vision": True, "tools": True},
                context_length=1048576
            ))
        return normalized

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    def generate(self, request: str, model_id: str, **kwargs) -> str:
        self._init_client()
        if not self._client:
            return f"[Error: Gemini SDK not initialized or missing API Key]"
        
        try:
            response = self._client.models.generate_content(
                model=model_id,
                contents=request,
            )
            return response.text
        except Exception as e:
            return f"[Gemini API Error: {str(e)}]"

    def stream(self, request: str, model_id: str, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield f"[Error: Gemini SDK not initialized or missing API Key]"
            return
            
        try:
            response = self._client.models.generate_content_stream(
                model=model_id,
                contents=request,
            )
            for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"[Gemini API Stream Error: {str(e)}]"

    def health_check(self) -> bool:
        return True

    def disconnect(self) -> None:
        CredentialManager.clear_api_key()
        self._is_authenticated = False
