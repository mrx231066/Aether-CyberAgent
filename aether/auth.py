"""Authentication module for Aether-CyberAgent."""

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
    """Dual Authentication Menu. Returns (api_key, model)"""
    config = load_config()
    api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY")
    model = config.get("model")

    if not api_key:
        console.print("\n[bold yellow]🔐 How would you like to authenticate?[/bold yellow]")
        console.print("[1] Login with Google (OAuth Browser Flow)")
        console.print("[2] Enter Gemini API Key Manually")
        
        choice = Prompt.ask("Select an option", choices=["1", "2"], default="2")
        
        if choice == "1":
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                # Assuming client_secrets.json is present in the current directory or home directory
                client_secrets = Path.home() / "client_secrets.json"
                if not client_secrets.exists():
                    console.print("[bold red]❌ client_secrets.json not found in home directory. Falling back to API Key.[/bold red]")
                    api_key = _prompt_api_key()
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secrets),
                        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
                    )
                    credentials = flow.run_local_server(port=0)
                    console.print(f"[green]✅ Authenticated via OAuth as {credentials.id_token}[/green]\n")
                    # In a real app we'd use this to get a GCP token, but for now we'll just save it if possible
                    # Gemini API generally requires an API Key or GCP service account.
                    # We will store a placeholder or actual key if retrieved.
                    api_key = credentials.token
                    os.environ["GEMINI_API_KEY"] = api_key
                    save_config({"api_key": api_key, "oauth": True})
            except Exception as e:
                console.print(f"[bold red]❌ OAuth flow failed: {e}[/bold red]")
                api_key = _prompt_api_key()
        else:
            api_key = _prompt_api_key()

    else:
        os.environ["GEMINI_API_KEY"] = api_key

    if not model:
        from aether.cli.interactive import _select_model
        model = _select_model(api_key)
        save_config({"model": model})

    return api_key, model

def _prompt_api_key() -> str:
    api_key = Prompt.ask("[bold cyan]🔑 Enter Gemini API Key (Input hidden for security)[/bold cyan]", password=True)
    if not api_key:
        console.print("[bold red]❌ API Key is required.[/bold red]")
        raise SystemExit(1)
    os.environ["GEMINI_API_KEY"] = api_key
    save_config({"api_key": api_key})
    console.print("[green]✅ API Key saved to ~/.aether_config.json[/green]\n")
    return api_key
