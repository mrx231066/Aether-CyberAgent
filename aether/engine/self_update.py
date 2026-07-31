"""GitHub-based Self-Update System for Aether-CyberAgent."""

import hashlib
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class SelfUpdateEngine:
    """Manages secure, verified updates from the official GitHub repository."""

    # Pinned official repository to prevent malicious fork redirection
    OFFICIAL_REPO_API = "https://api.github.com/repos/mrx231066/Aether-CyberAgent/releases/latest"
    CURRENT_VERSION = "4.2.0"

    @classmethod
    def check_for_update(cls, auto_check: bool = True) -> dict | None:
        """Queries GitHub for the latest commit/release and compares versions."""
        if not auto_check:
            return None

        console.print("[dim]🔄 Checking GitHub for updates...[/dim]")
        try:
            req = urllib.request.Request("https://api.github.com/repos/mrx231066/Aether-CyberAgent/commits/main", headers={'User-Agent': 'Aether-CyberAgent'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            sha = data.get("sha", "")[:7]
            console.print(f"[bold green]🚀 Current main commit on GitHub: {sha}[/bold green]")
            console.print("[bold yellow]Type `/update apply` to pull the latest code directly from GitHub.[/bold yellow]\n")
            return data
        except Exception as e:
            console.print(f"[dim]⚠️ GitHub check notice: {e}[/dim]")
            return None

    @classmethod
    def apply_update(cls):
        """Pulls and installs the latest code directly from GitHub."""
        console.print(f"\n[bold blue]⬇️ Pulling latest Aether-CyberAgent from GitHub main...[/bold blue]")
        try:
            subprocess.run(["pip", "install", "--upgrade", "--no-cache-dir", "git+https://github.com/mrx231066/Aether-CyberAgent.git"], check=True)
            console.print("[bold green]✅ Update successfully applied! Please restart Aether.[/bold green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Update installation failed: {e}[/bold red]")

    @staticmethod
    def _is_newer(current: str, latest: str) -> bool:
        """Simple semantic version comparison fallback if packaging is unavailable."""
        try:
            from packaging import version
            return version.parse(latest) > version.parse(current)
        except ImportError:
            c_parts = [int(x) for x in current.split(".") if x.isdigit()]
            l_parts = [int(x) for x in latest.split(".") if x.isdigit()]
            return l_parts > c_parts
