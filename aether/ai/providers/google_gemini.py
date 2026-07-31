"""Google Gemini Provider Adapter for Aether-CyberAgent."""

import os
import json
from pathlib import Path
from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata
from aether.ai.providers.helpers import get_cached_models, set_cached_models
from aether.engine.credentials import CredentialManager

console = Console()

class GoogleGeminiAdapter(AetherProvider):
    
    name = "google_gemini"
    display_name = "Google Gemini"
    
    def __init__(self):
        self._is_authenticated = False
        self._auth_method = "none"
        self._client = None
        self._oauth_credentials = None

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
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            client_secrets = Path.home() / "client_secrets.json"
            if not client_secrets.exists():
                console.print("[yellow]⚠️ client_secrets.json not found in home directory.[/yellow]")
                console.print("[cyan]Falling back to Gemini API Key authentication...[/cyan]\n")
                return self._auth_api_key()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets),
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            )
            console.print("[bold cyan]Opening local server for OAuth... please follow the link provided below![/bold cyan]")
            credentials = flow.run_local_server(port=0, open_browser=False)
            console.print(f"[green]✅ Authenticated via OAuth![/green]\n")
            
            self._oauth_credentials = credentials
            self._is_authenticated = True
            self._auth_method = "oauth"
            
            try:
                cred_info = {
                    "token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "scopes": credentials.scopes
                }
                CredentialManager.save_credential("google_gemini_oauth", json.dumps(cred_info))
            except Exception:
                pass
                
            self._init_client()
            return True
        except Exception as e:
            console.print(f"[dim yellow]OAuth flow unavailable ({e}). Falling back to Gemini API Key...[/dim yellow]\n")
            return self._auth_api_key()

    def _auth_api_key(self) -> bool:
        api_key = Prompt.ask("Enter Gemini API Key", password=True)
        if not api_key:
            console.print("[red]❌ No API Key entered.[/red]")
            return False
        CredentialManager.save_credential("google_gemini", api_key)
        self._is_authenticated = True
        self._auth_method = "api_key"
        self._init_client()
        return True

    def _init_client(self):
        try:
            from google import genai
            
            if hasattr(self, "_oauth_credentials") and self._oauth_credentials:
                self._client = genai.Client(credentials=self._oauth_credentials)
                return

            oauth_json = CredentialManager.get_credential("google_gemini_oauth")
            if oauth_json:
                try:
                    from google.oauth2.credentials import Credentials
                    cred_dict = json.loads(oauth_json)
                    creds = Credentials.from_authorized_user_info(cred_dict)
                    self._oauth_credentials = creds
                    self._client = genai.Client(credentials=creds)
                    return
                except Exception:
                    pass

            api_key = CredentialManager.get_credential("google_gemini")
            if api_key:
                self._client = genai.Client(api_key=api_key)
        except Exception:
            pass

    def validate_credentials(self) -> bool:
        return (
            getattr(self, "_oauth_credentials", None) is not None or
            CredentialManager.get_credential("google_gemini_oauth") is not None or
            CredentialManager.get_credential("google_gemini") is not None
        )

    def list_models(self, force_refresh: bool = False) -> List[ModelMetadata]:
        if not force_refresh:
            cached = get_cached_models(self.name)
            if cached:
                return cached

        self._init_client()
        if not self._client:
            raise RuntimeError("Google Gemini client not authenticated or missing API Key/OAuth Credentials.")

        try:
            # Live model discovery via google-genai SDK
            models = self._client.models.list()
            result = []
            for m in models:
                name = getattr(m, "name", "")
                disp = getattr(m, "display_name", name)
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
        except Exception as e:
            raise RuntimeError(f"Google Gemini live model discovery failed: {e}")

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
            return f"[Error: Gemini SDK not initialized or missing API Key/OAuth Credentials]"
        
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
            return f"[Gemini API Error: {str(e)}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        self._init_client()
        if not self._client:
            yield f"[Error: Gemini SDK not initialized or missing API Key/OAuth Credentials]"
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
            yield f"[Gemini API Stream Error: {str(e)}]"

    def health_check(self) -> bool:
        return self.validate_credentials()

    def disconnect(self) -> None:
        CredentialManager.clear_credential("google_gemini")
        CredentialManager.clear_credential("google_gemini_oauth")
        self._oauth_credentials = None
        self._is_authenticated = False
        self._client = None
