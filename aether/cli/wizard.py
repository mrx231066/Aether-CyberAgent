"""Interactive Setup Wizard for Aether-CyberAgent v4.0.0"""
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from aether.cli.theme_engine import ThemeEngine, THEME_PRESETS
from aether.config import Config
from pathlib import Path
import json

console = Console()
CONFIG_PATH = Path(".aether_config.json")

class SetupWizard:
    @staticmethod
    def run_wizard():
        console.print(Panel("[bold cyan]Welcome to Aether-CyberAgent Setup Wizard[/bold cyan]", border_style="cyan"))
        
        # 1. Authentication
        auth_type = Prompt.ask("Select Authentication Type", choices=["API Key", "Google OAuth"], default="API Key")
        if auth_type == "API Key":
            api_key = Prompt.ask("Enter your Gemini API Key", password=True)
            config_data = {"api_key": api_key, "auth_type": "api_key"}
        else:
            console.print("[dim]Google OAuth selected...[/dim]")
            config_data = {"auth_type": "oauth"}
            
        # 2. Model Provider
        provider = Prompt.ask("Select Primary Model Provider", choices=["Gemini", "Ollama", "Anthropic", "DeepSeek"], default="Gemini")
        config_data["provider"] = provider.lower()
        
        # 3. Theme
        console.print("\n[bold]Available Themes:[/bold]")
        theme_names = list(THEME_PRESETS.keys())
        for idx, t in enumerate(theme_names):
            color = THEME_PRESETS[t]["primary"]
            console.print(f"[{color}] {idx+1}. {t} [/]")
            
        theme_idx = Prompt.ask("Select Theme Number", choices=[str(i+1) for i in range(len(theme_names))], default="1")
        theme_name = theme_names[int(theme_idx)-1]
        ThemeEngine.set_theme(theme_name)
        
        config_data["theme"] = theme_name
        
        # Save config
        if CONFIG_PATH.exists():
            try:
                curr = json.loads(CONFIG_PATH.read_text())
                curr.update(config_data)
                config_data = curr
            except Exception:
                pass
        CONFIG_PATH.write_text(json.dumps(config_data, indent=2))
        console.print(Panel(f"[bold green]Setup Complete![/bold green]\nTheme: {theme_name}\nProvider: {provider}", border_style="green"))
