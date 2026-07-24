"""Hybrid LLM Router for Aether-CyberAgent v1.0.0"""
from aether.config import Config
from aether.ai.local_llm import OllamaClient
from rich.console import Console

console = Console()

class HybridRouter:
    @staticmethod
    def route_task(task_type: str, prompt: str, system: str = "") -> str:
        """Routes lightweight tasks to local models, heavy tasks to cloud."""
        # Lightweight tasks like NL-to-Shell can use local models if available.
        if task_type == "lightweight" or Config.OFFLINE_MODE:
            client = OllamaClient()
            if client.is_available():
                console.print("[dim]⚡ Routing to local Ollama (qwen-coder)...[/dim]")
                return client.generate(model="qwen-coder", prompt=prompt, system=system)
            else:
                if Config.OFFLINE_MODE:
                    console.print("[bold red]❌ Offline Mode active but Ollama is unreachable.[/bold red]")
                    return ""
                # Fallthrough to cloud
                
        # If heavy task or local unavailable, use primary cloud provider
        # Note: In a full multi-provider setup, this calls the unified API interface.
        console.print("[dim]☁️  Routing to primary Cloud Provider...[/dim]")
        # Placeholder for unified provider call
        from aether.ai.gemini_client import GeminiClient
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return ""
        try:
            client = GeminiClient(api_key=api_key)
            return client.chat(prompt)
        except Exception:
            return ""
