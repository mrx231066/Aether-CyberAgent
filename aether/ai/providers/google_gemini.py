"""Google Gemini Provider Adapter for Aether-CyberAgent.

Uses direct Google AI Studio API Key authentication via official google-genai SDK.
Live model discovery is enforced via client.models.list().
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

        # Immediate validation on entry before saving
        try:
            from google import genai
            test_client = genai.Client(api_key=api_key)
            models = list(test_client.models.list())
            if not models:
                console.print("[red]❌ Google Gemini API returned no models.[/red]")
                return False
            self._client = test_client
        except Exception as e:
            console.print(f"[bold red]❌ Invalid, expired, or API call failed for Gemini API Key: {e}[/bold red]")
            return False

        CredentialManager.save_credential("google_gemini", api_key)
        self._is_authenticated = True
        console.print("[bold green]✅ Google Gemini connected & key verified successfully![/bold green]")
        return True

    def _init_client(self) -> bool:
        if self._client:
            return True
            
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
            # Direct live discovery from client.models.list() — NO hardcoded fallback arrays
            models = self._client.models.list()
            result = []
            for m in models:
                name = getattr(m, "name", "") or ""
                disp = getattr(m, "display_name", "") or name
                methods = getattr(m, "supported_generation_methods", []) or []
                
                # Filter for Gemini models supporting generateContent if methods specified
                if "gemini" in name.lower() and (not methods or "generateContent" in methods or "generate_content" in methods):
                    clean_id = name.replace("models/", "") if name.startswith("models/") else name
                    result.append(ModelMetadata(
                        provider=self.name,
                        provider_display_name=self.display_name,
                        model_id=clean_id,
                        display_name=disp or clean_id,
                        capabilities={"streaming": True, "vision": True, "tools": True},
                        context_length=getattr(m, "input_token_limit", 1048576) or 1048576
                    ))

            if not result:
                raise ValueError("No Gemini models supporting generateContent returned by Google GenAI API.")

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
            models = self.list_models()
            target_model = models[0].model_id

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=AETHER_IDENTITY_PROMPT
            )
            response = self._client.models.generate_content(
                model=target_model,
                contents=request,
                config=config,
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
            models = self.list_models()
            target_model = models[0].model_id

        try:
            from aether.ai.prompt_builder import AETHER_IDENTITY_PROMPT
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=AETHER_IDENTITY_PROMPT
            )
            response = self._client.models.generate_content_stream(
                model=target_model,
                contents=request,
                config=config,
            )
            for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"[Gemini Stream Error (Credentials invalid/expired or API error): {str(e)}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("google_gemini")
        self._is_authenticated = False
        self._client = None
