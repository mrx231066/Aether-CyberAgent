"""Local LLM Client for Aether-CyberAgent v1.0.0"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, model: str, prompt: str, system: Optional[str] = None) -> str:
        url = f"{self.host}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            data["system"] = system
            
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            console.print(f"[red]Ollama generation failed: {e}[/red]")
            return ""
