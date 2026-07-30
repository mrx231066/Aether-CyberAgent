"""Hybrid LLM Router for Aether-CyberAgent v4.0.0"""
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
        console.print("[dim]☁️  Routing to primary Cloud Provider...[/dim]")
        
        from aether.ai.provider_manager import ProviderManager
        provider = ProviderManager.get_active_provider()
        
        if not provider:
            console.print("[bold red]❌ No active cloud provider configured. Use /provider add[/bold red]")
            return ""
            
        model_id = ProviderManager._active_model_id
        if not model_id:
            # Fallback to the first available model if one isn't explicitly set
            models = provider.list_models()
            if models:
                model_id = models[0].model_id
                ProviderManager._active_model_id = model_id
            else:
                return "[Error: Provider has no available models]"
                
        try:
            return provider.generate(request=f"System: {system}\n\nUser: {prompt}", model_id=model_id)
        except Exception as e:
            return f"[Provider Error: {str(e)}]"
