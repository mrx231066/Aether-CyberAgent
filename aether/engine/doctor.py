"""Aether System Doctor Diagnostic Engine (v4.0.1).

Performs full environment, dependency, credential, provider, database,
and resource diagnostics.
"""

import sys
import os
import shutil
import platform
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

class DoctorEngine:
    """Diagnostic suite for checking Aether runtime health."""

    @classmethod
    def run_diagnostics(cls) -> Dict[str, Any]:
        results = {}
        
        # 1. Python Environment
        results["python"] = {
            "status": "PASS" if sys.version_info >= (3, 10) else "WARN",
            "version": f"{platform.python_version()} ({sys.executable})",
        }

        # 2. Git CLI
        git_path = shutil.which("git")
        results["git"] = {
            "status": "PASS" if git_path else "FAIL",
            "detail": git_path or "Git not found in PATH",
        }

        # 3. Node.js
        node_path = shutil.which("node")
        results["node"] = {
            "status": "PASS" if node_path else "INFO",
            "detail": node_path or "Node.js not installed (optional)",
        }

        # 4. Docker
        docker_path = shutil.which("docker")
        results["docker"] = {
            "status": "PASS" if docker_path else "INFO",
            "detail": docker_path or "Docker not installed (optional)",
        }

        # 5. Ollama Local LLM
        try:
            import httpx
            resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
            ollama_status = "PASS" if resp.status_code == 200 else "INFO"
            ollama_detail = f"Online ({len(resp.json().get('models', []))} models)" if resp.status_code == 200 else "Offline"
        except Exception:
            ollama_status = "INFO"
            ollama_detail = "Offline / Not running"

        results["ollama"] = {"status": ollama_status, "detail": ollama_detail}

        # 6. Database Check
        from aether.engine.db import AetherDB
        integrity = AetherDB.check_integrity()
        results["database"] = {
            "status": integrity["status"],
            "detail": f"SQLite WAL ({integrity['details']})",
        }

        # 7. Credential Store
        from aether.engine.credentials import CredentialManager
        stored_providers = CredentialManager.list_stored_providers()
        results["credentials"] = {
            "status": "PASS" if stored_providers or os.environ.get("GEMINI_API_KEY") else "WARN",
            "detail": f"Stored for: {', '.join(stored_providers)}" if stored_providers else "No credentials saved",
        }

        # 8. Active Provider & Model
        from aether.ai.provider_manager import ProviderManager
        active_provider = ProviderManager.get_active_provider()
        results["active_provider"] = {
            "status": "PASS" if active_provider else "WARN",
            "detail": f"{active_provider.display_name} ({ProviderManager._active_model_id or 'No model'})" if active_provider else "None (Offline mode)",
        }

        # 9. Disk & Workspace
        disk = shutil.disk_usage(Path.cwd())
        free_gb = disk.free / (1024 ** 3)
        results["disk"] = {
            "status": "PASS" if free_gb > 1.0 else "WARN",
            "detail": f"{free_gb:.1f} GB free in {Path.cwd()}",
        }

        # 10. Plugins & Skills
        from aether.engine.skills import SkillsLoader
        skills = SkillsLoader.discover_skills()
        results["skills"] = {
            "status": "PASS",
            "detail": f"{len(skills)} skill(s) loaded",
        }

        return results

    @classmethod
    def display_report(cls):
        console.print("\n╭─────────────────────────────────────────────╮")
        console.print("│              [bold cyan]🩺 AETHER DOCTOR[/bold cyan]                │")
        console.print("├─────────────────────────────────────────────┤")

        results = cls.run_diagnostics()

        table = Table(box=box.ROUNDED, border_style="cyan")
        table.add_column("Component", style="bold yellow")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="white")

        status_styles = {
            "PASS": "[bold green]✓ PASS[/bold green]",
            "WARN": "[bold yellow]⚠️  WARN[/bold yellow]",
            "FAIL": "[bold red]❌ FAIL[/bold red]",
            "INFO": "[dim cyan]ℹ️  INFO[/dim cyan]",
        }

        for comp, info in results.items():
            status_fmt = status_styles.get(info["status"], info["status"])
            table.add_row(comp.capitalize().replace("_", " "), status_fmt, info["detail"])

        console.print(table)
        console.print("╰─────────────────────────────────────────────╯\n")
