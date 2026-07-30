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
    CURRENT_VERSION = "2.0.0"

    @classmethod
    def check_for_update(cls, auto_check: bool = True) -> dict | None:
        """Queries GitHub for the latest release and compares versions."""
        if not auto_check:
            return None

        console.print("[dim]🔄 Checking for updates...[/dim]")
        try:
            req = urllib.request.Request(cls.OFFICIAL_REPO_API, headers={'User-Agent': 'Aether-CyberAgent'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("tag_name", "").lstrip("v")
            
            if cls._is_newer(cls.CURRENT_VERSION, latest_version):
                console.print(f"\n[bold green]🚀 New Aether-CyberAgent version available: v{latest_version} (Current: v{cls.CURRENT_VERSION})[/bold green]")
                console.print(f"[dim]Changelog:\n{data.get('body', 'No release notes provided.')}[/dim]")
                console.print("\n[bold yellow]Type `/update apply` to install the update safely.[/bold yellow]\n")
                return data
            else:
                console.print("[dim]✅ Aether-CyberAgent is up to date.[/dim]")
                return None
        except Exception as e:
            console.print(f"[dim]⚠️ Failed to check for updates: {e}[/dim]")
            return None

    @classmethod
    def apply_update(cls):
        """Applies the update after explicit user confirmation."""
        # 1. Fetch latest version info
        try:
            req = urllib.request.Request(cls.OFFICIAL_REPO_API, headers={'User-Agent': 'Aether-CyberAgent'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
        except Exception as e:
            console.print(f"[bold red]❌ Failed to fetch update info: {e}[/bold red]")
            return

        latest_version = data.get("tag_name", "").lstrip("v")
        if not cls._is_newer(cls.CURRENT_VERSION, latest_version):
            console.print("[green]✅ You are already on the latest version.[/green]")
            return

        # 2. Strict Confirmation (Never bypassed)
        console.print(f"\n[bold red]⚠️ UPDATE CONFIRMATION[/bold red]")
        console.print(f"You are about to update from [yellow]v{cls.CURRENT_VERSION}[/yellow] to [green]v{latest_version}[/green].")
        if not Confirm.ask("[bold white]Do you explicitly authorize applying this update?[/bold white]"):
            console.print("[dim]Update cancelled by user.[/dim]")
            return

        # 3. Apply Update
        console.print(f"\n[bold blue]⬇️ Pulling source update for v{latest_version}...[/bold blue]")
        try:
            # Source install path
            subprocess.run(["pip", "install", "--upgrade", "aether-cyberagent"], check=True)
            
            # Future binary path: Download asset -> verify SHA256 -> swap binary
            # TODO (Phase 2 - Nuitka): Implement asset checksum verification here
            
            # 4. Log the update via Silver Guardian / Audit Log
            from aether.engine.quota import AuditLogger
            AuditLogger.log_event("SELF_UPDATE", "APPLY_UPDATE", f"Upgraded {cls.CURRENT_VERSION} -> {latest_version}")
            
            console.print("[bold green]✅ Update successfully applied! Please restart Aether-CyberAgent.[/bold green]")
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
