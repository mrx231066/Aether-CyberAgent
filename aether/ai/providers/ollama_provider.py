"""Ollama Local Model Provider Adapter for Aether-CyberAgent."""

from typing import List, Optional, Any
from rich.console import Console
from rich.prompt import Prompt
from aether.ai.providers.base import AetherProvider, ModelMetadata

console = Console()


class OllamaAdapter(AetherProvider):

    name = "ollama"
    display_name = "Ollama (Local)"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url
        self._is_authenticated = True

    def authenticate(self) -> bool:
        console.print("\n╭──────────────────────────────────────╮")
        console.print("│       [bold green]OLLAMA LOCAL SETUP[/bold green]             │")
        console.print("╰──────────────────────────────────────╯")
        url = Prompt.ask("Ollama URL", default=self._base_url)
        self._base_url = url
        if self.health_check():
            console.print("[bold green]✅ Connected to Ollama![/bold green]")
            return True
        console.print("[red]❌ Cannot reach Ollama at {self._base_url}. Is it running?[/red]")
        return False

    def validate_credentials(self) -> bool:
        return True

    def list_models(self) -> List[ModelMetadata]:
        try:
            import httpx
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [
                    ModelMetadata(
                        provider=self.name,
                        provider_display_name=self.display_name,
                        model_id=m["name"],
                        display_name=m["name"],
                        capabilities={"streaming": True, "local": True},
                        context_length=0,
                    ) for m in data.get("models", [])
                ]
        except Exception:
            pass
        return []

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    def generate(self, request: str, model_id: Optional[str] = None, **kwargs) -> str:
        models = self.list_models()
        target_model = model_id or (models[0].model_id if models else "llama3")
        try:
            import httpx
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": target_model, "prompt": request, "stream": False},
                timeout=120,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
            return f"[Ollama Error: HTTP {resp.status_code}]"
        except Exception as e:
            return f"[Ollama Error: {e}]"

    def stream(self, request: str, model_id: Optional[str] = None, **kwargs) -> Any:
        models = self.list_models()
        target_model = model_id or (models[0].model_id if models else "llama3")
        try:
            import httpx
            with httpx.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={"model": target_model, "prompt": request, "stream": True},
                timeout=120,
            ) as resp:
                import json
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
        except Exception as e:
            yield f"[Ollama Stream Error: {e}]"

    def health_check(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def disconnect(self) -> None:
        self._is_authenticated = False
