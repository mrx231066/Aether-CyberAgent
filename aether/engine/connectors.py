"""Omni-Connectors for Aether-CyberAgent."""

import subprocess
from rich.console import Console

console = Console()

def adb_connector(command: str) -> str:
    """Execute Android Debug Bridge commands."""
    try:
        res = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
        if "device offline" in res.stderr or "no devices/emulators found" in res.stderr:
            console.print("[yellow]ADB disconnected. Attempting to start server...[/yellow]")
            subprocess.run("adb start-server", shell=True, capture_output=True)
            res = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else res.stderr
    except Exception as e:
        return f"ADB Error: {e}"

def github_connector(action: str, target: str) -> str:
    """Interface with local Git CLI."""
    try:
        if action == "status":
            cmd = "git status"
        elif action == "commit":
            cmd = f"git commit -m \"{target}\""
        elif action == "push":
            cmd = "git push"
        elif action == "add":
            cmd = f"git add {target}"
        else:
            return "Unknown git action"
            
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else res.stderr
    except Exception as e:
        return f"Git Error: {e}"

def gmail_connector() -> str:
    """Stub function for future email integrations."""
    return "Gmail connector is currently a stub for future integrations."
