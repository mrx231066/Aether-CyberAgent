"""Authentication module for Aether-CyberAgent (Gemini API Key Authentication)."""

import os
import json
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt

console = Console()
CONFIG_PATH = Path.home() / ".aether_config.json"

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_config(data: dict) -> None:
    try:
        config = load_config()
        config.update(data)
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as e:
        console.print(f"[dim yellow]Warning: Could not save config: {e}[/dim yellow]")

def authenticate() -> Tuple[Optional[str], Optional[str]]:
    """Authentication setup using Gemini API Key."""
    config = load_config()
    api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY")
    model = config.get("model")

    if not api_key:
        api_key = _prompt_api_key()
    else:
        os.environ["GEMINI_API_KEY"] = api_key

    if not model:
        from aether.cli.interactive import _select_model
        model = _select_model(api_key)
        save_config({"model": model})

    return api_key, model

def _prompt_api_key() -> str:
    console.print("[dim]Get your API key from Google AI Studio: https://aistudio.google.com/app/apikey[/dim]")
    api_key = Prompt.ask("[bold cyan]🔑 Enter Gemini API Key (Input hidden for security)[/bold cyan]", password=True)
    if not api_key:
        console.print("[bold red]❌ API Key is required.[/bold red]")
        raise SystemExit(1)
    os.environ["GEMINI_API_KEY"] = api_key
    save_config({"api_key": api_key})
    console.print("[green]✅ API Key saved.[/green]\n")
    return api_key
