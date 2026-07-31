"""Google Gemini Provider Adapter for Aether-CyberAgent.

Uses standard Google AI Studio API Key authentication via official google-genai SDK.
"""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.helpers import get_cached_models, set_cached_models
from aether.engine.credentials import CredentialManager

console = Console()


class GoogleGeminiAdapter(AetherProvider):
    """Adapter for Google Gemini API via google-genai SDK (API Key authentication)."""
    
    name = "google_gemini"
    display_name = "Google Gemini"
    
    def __init__(self):
        self._is_authenticated = False
        self._client = None

    def authenticate(self) -> bool:
        console.print("\n╭──────────────────────────────────────╮")
        console.print("│       [bold blue]GOOGLE GEMINI SETUP[/bold blue]            │")
        console.print("╰──────────────────────────────────────╯")
        console.print("[dim]Get your API key from Google AI Studio: https://aistudio.google.com/app/apikey[/dim]\n")
        
        api_key = Prompt.ask("Enter Gemini API Key", password=True)
        if not api_key:
            console.print("[red]❌ No API Key entered.[/red]")
            return False

        CredentialManager.save_credential("google_gemini", api_key)
        self._is_authenticated = True
        return self._init_client()

    def _init_client(self) -> bool:
        api_key = CredentialManager.get_credential("google_gemini")
        if not api_key:
            self._client = None
            return False

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            return True
        except Exception as e:
            console.print(f"[bold red]❌ Failed to initialize Google GenAI SDK: {e}[/bold red]")
            self._client = None
            return False

    def validate_credentials(self) -> bool:
        return CredentialManager.get_credential("google_gemini") is not None

    def list_models(self, force_refresh: bool = False) -> List[ModelMetadata]:
        if not force_refresh:
            cached = get_cached_models(self.name)
            if cached:
                return cached

        api_key = CredentialManager.get_credential("google_gemini")
        if not api_key:
            raise RuntimeError("No credentials provided: Google Gemini API Key is missing. Please set it via /provider add.")

        if not self._client:
            if not self._init_client():
                raise RuntimeError("Failed to initialize Google GenAI client instance.")

        try:
            models = self._client.models.list()
            result = []
            for m in models:
                name = getattr(m, "name", "") or ""
                disp = getattr(m, "display_name", "") or name
                if "gemini" in name.lower():
                    clean_id = name.replace("models/", "") if name.startswith("models/") else name
                    result.append(ModelMetadata(
                        provider=self.name,
                        provider_display_name=self.display_name,
                        model_id=clean_id,
                        display_name=disp or clean_id,
                        capabilities={"streaming": True, "vision": True, "tools": True},
                        context_length=1048576
                    ))

            if not result:
                raise ValueError("No Gemini models returned by Google GenAI API.")

            sorted_result = sorted(result, key=lambda x: x.model_id)
            set_cached_models(self.name, sorted_result)
            return sorted_result
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Credentials provided but invalid, expired, or API call failed: {e}")

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        try:
            for m in self.list_models():
                if m.model_id == model_id:
                    return m
        except Exception:
            pass
        return None

    def generate(self, request: str, model_id: Optional[str] = None, **kwargs) -> str:
        if not self._client and not self._init_client():
            return "[Error: No credentials provided — Google Gemini API Key missing]"
        
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "gemini-2.5-pro"
            except Exception:
                target_model = "gemini-2.5-pro"

        try:
            response = self._client.models.generate_content(
                model=target_model,
                contents=request,
            )
            return response.text
        except Exception as e:
            return f"[Gemini API Error (Credentials invalid/expired or API error): {str(e)}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        if not self._client and not self._init_client():
            yield "[Error: No credentials provided — Google Gemini API Key missing]"
            return
            
        target_model = model_id
        if not target_model:
            try:
                models = self.list_models()
                target_model = models[0].model_id if models else "gemini-2.5-pro"
            except Exception:
                target_model = "gemini-2.5-pro"

        try:
            response = self._client.models.generate_content_stream(
                model=target_model,
                contents=request,
            )
            for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"[Gemini Stream Error (Credentials invalid/expired or API error): {str(e)}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("google_gemini")
        CredentialManager.clear_credential("google_gemini_oauth")
        self._is_authenticated = False
        self._client = None
