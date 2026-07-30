"""Aether-CyberAgent CLI: The command-line interface.

Entry point for the `aether` command. Provides scan, verify, and dashboard
subcommands powered by the full multi-agent pipeline.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.tree import Tree
from rich import box

app = typer.Typer(
    name="aether",
    help="🛡️ Aether-CyberAgent: Autonomous Multi-Agent AI Security Platform",
    add_completion=False,
)
console = Console()

CONFIG_PATH = Path(".aether_config.json")

BANNER = """[bold cyan]
   ╔═══════════════════════════════════════════════╗
   ║          🛡️  AETHER-CYBERAGENT  🛡️            ║
   ║   Autonomous Multi-Agent AI Security Platform  ║
   ║            v4.0.0 · Defense Only               ║
   ╚═══════════════════════════════════════════════╝
[/bold cyan]"""


def load_aether_config() -> dict:
    """Load configuration from local .aether_config.json."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_aether_config(data: dict) -> None:
    """Save/update configuration in local .aether_config.json."""
    try:
        config = load_aether_config()
        config.update(data)
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as e:
        console.print(f"[dim yellow]Warning: Could not save config to {CONFIG_PATH}: {e}[/dim yellow]")


def select_model_interactively(api_key: Optional[str] = None) -> str:
    """Prompt user to select a Gemini model from discovered available models."""
    from aether.ai.gemini_client import GeminiClient

    console.print("\n[bold cyan]🔍 Discovering available Google Gemini models...[/bold cyan]")
    available_models = GeminiClient.get_available_models(api_key=api_key)

    if not sys.stdin.isatty():
        default_model = available_models[0]["name"] if available_models else GeminiClient.DEFAULT_MODEL
        console.print(f"[dim]Non-interactive environment detected. Using default model: {default_model}[/dim]")
        return default_model

    table = Table(title="🤖 Discovered Gemini Models", box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="bold yellow", justify="right")
    table.add_column("Model Name", style="bold white")
    table.add_column("Info", style="green")

    for idx, m_dict in enumerate(available_models, 1):
        name = m_dict.get("name", "")
        info = m_dict.get("info", "")
        rec = "⭐ Recommended" if name == GeminiClient.DEFAULT_MODEL else info
        table.add_row(str(idx), name, rec)

    console.print(table)

    choices = [str(i) for i in range(1, len(available_models) + 1)]
    choice = Prompt.ask(
        "\n[bold yellow]Select a model number[/bold yellow]",
        choices=choices,
        default="1",
    )
    selected = available_models[int(choice) - 1]["name"]
    console.print(f"[bold green]Selected model: {selected}[/bold green]\n")
    return selected



@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    skip_all_permissions: bool = typer.Option(False, "--skip-all-permissions", help="Enable Omni-Agent God Mode"),
    setup: bool = typer.Option(False, "--setup", help="Run interactive setup wizard"),
    web: bool = typer.Option(False, "--web", help="Launch WebSocket Visualizer Sidecar")
):
    """Aether-CyberAgent: Autonomous AI Security Platform."""
    from aether.engine.integrity import verify_self_integrity
    verify_self_integrity()
    
    from aether.config import Config
    if skip_all_permissions:
        Config.GOD_MODE = True
        console.print("[bold red]⚡ GOD MODE ACTIVATED: Skipping all permissions.[/bold red]")

    if setup:
        from aether.cli.wizard import SetupWizard
        SetupWizard.run_wizard()
        return

    if web:
        from aether.web.server import run_server
        run_server()
        return

    if ctx.invoked_subcommand is None:
        os.system('clear' if os.name == 'posix' else 'cls')
        from aether.cli.interactive import start_interactive_session
        start_interactive_session()


@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to scan for vulnerabilities"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    max_retries: int = typer.Option(3, "--max-retries", "-r", help="Max self-healing retries"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY", help="Gemini API key"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Gemini model to use (e.g. gemini-2.5-pro)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Force interactive model selection"),
):
    """🔵 Run a full autonomous security scan on the target path."""
    console.print(BANNER)

    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[bold red]❌ Path does not exist: {path}[/bold red]")
        raise typer.Exit(code=1)

    # 1. API Key Prompt & Validation
    config = load_aether_config()
    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY") or config.get("api_key")

    if not effective_api_key:
        if sys.stdin.isatty():
            effective_api_key = Prompt.ask(
                "[bold yellow]🔑 GEMINI_API_KEY not found. Enter your Google Gemini API Key[/bold yellow]",
                password=True,
            )
            if not effective_api_key:
                console.print("[bold red]❌ API Key is required to run AI remediation.[/bold red]")
                raise typer.Exit(code=1)
            os.environ["GEMINI_API_KEY"] = effective_api_key
            save_aether_config({"api_key": effective_api_key})
        else:
            console.print("[bold red]❌ GEMINI_API_KEY not found in environment or config.[/bold red]")
            raise typer.Exit(code=1)
    else:
        os.environ["GEMINI_API_KEY"] = effective_api_key

    # 2. Dynamic Model Selection Logic
    selected_model: str
    if model:
        selected_model = model
        save_aether_config({"model": selected_model})
        console.print(f"[bold cyan]🤖 Using specified model: [white]{selected_model}[/white][/bold cyan]")
    elif config.get("model") and not interactive:
        selected_model = config["model"]
        console.print(f"[bold cyan]🤖 Using saved model preference: [white]{selected_model}[/white][/bold cyan]")
    else:
        selected_model = select_model_interactively(api_key=effective_api_key)
        save_aether_config({"model": selected_model})

    from aether.agents.gold_autonomic import AutonomicEngine
    from aether.reports.sarif import SarifReporter
    from aether.reports.html_report import HtmlReporter
    from aether.agents.red_attacker import RedTeamAttacker

    try:
        engine = AutonomicEngine(max_retries=max_retries, api_key=effective_api_key, model=selected_model)
        result = engine.execute_scan(str(target))

        # Red Team attack surface enumeration
        console.print("\n[bold red]🔴 Red Team: Running attack surface enumeration...[/bold red]")
        red_team = RedTeamAttacker()
        red_report = red_team.enumerate_attack_surface(str(target))

        # Generate SARIF report
        red_report_for_html = red_report
        if result.vulnerabilities_found > 0 or red_report.vectors:
            reporter = SarifReporter()
            sarif_path = reporter.export_from_pipeline(result, ".aether/reports")
            console.print(f"\n[bold white]📋 SARIF report saved: {sarif_path}[/bold white]")

            # Generate HTML report
            html_reporter = HtmlReporter()
            html_path = html_reporter.export_from_pipeline(result, ".aether/reports", red_report_for_html)
            console.print(f"[bold white]📄 HTML report saved: {html_path}[/bold white]")

        # Display final directory tree
        if result.verified_patches:
            tree = Tree("🛡️ [bold cyan]Patched Files[/bold cyan]")
            for patch in result.verified_patches:
                branch = tree.add(f"[green]✅ {patch['file']}[/green]")
                branch.add(f"[dim]{patch['vulnerability_title']}[/dim]")
                branch.add(f"[dim]Severity: {patch['severity']}[/dim]")
                branch.add(f"[dim]Attempts: {patch['attempts']}[/dim]")
            console.print(tree)

        if result.success:
            console.print("\n[bold green]✅ All vulnerabilities patched and verified![/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️  {len(result.failed_patches)} patches failed verification.[/bold yellow]")

    except ValueError as e:
        console.print(f"[bold red]❌ Configuration error: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]❌ Scan failed: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def verify(
    path: str = typer.Argument(..., help="Path to a Python file to verify"),
):
    """🟣 Run Purple Team formal verification on a specific file."""
    console.print(BANNER)

    target = Path(path).resolve()
    if not target.exists() or not target.suffix == ".py":
        console.print(f"[bold red]❌ Invalid Python file: {path}[/bold red]")
        raise typer.Exit(code=1)

    from aether.agents.purple_verifier import PurpleTeamVerifier

    source_code = target.read_text()
    verifier = PurpleTeamVerifier()

    console.print(f"[bold magenta]🟣 Purple Team: Verifying {target.name}...[/bold magenta]")

    result = verifier.verify_patch(
        original_code=source_code,
        patched_code=source_code,
        vulnerability_type="general",
    )

    if result.passed:
        console.print("[bold green]✅ Verification PASSED[/bold green]")
        for detail in result.details:
            console.print(f"  [dim]{detail}[/dim]")
    else:
        console.print("[bold red]❌ Verification FAILED[/bold red]")
        for detail in result.details:
            console.print(f"  [dim]{detail}[/dim]")
        if result.error_trace:
            console.print(f"\n[dim]Error trace:\n{result.error_trace}[/dim]")
        raise typer.Exit(code=1)


@app.command()
def dashboard():
    """📊 Launch the Aether real-time Streamlit dashboard."""
    console.print(BANNER)
    console.print("[bold blue]📊 Starting Aether Dashboard...[/bold blue]")
    console.print("[dim]Dashboard will open at http://localhost:8501[/dim]\n")

    dashboard_path = Path(__file__).parent.parent / "dashboard" / "app.py"
    if not dashboard_path.exists():
        console.print("[bold red]❌ Dashboard app not found.[/bold red]")
        raise typer.Exit(code=1)

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
        check=False,
    )


@app.command()
def watch(
    path: str = typer.Argument(".", help="Path to watch for changes"),
    debounce: float = typer.Option(2.0, "--debounce", "-d", help="Debounce delay in seconds"),
):
    """🔄 Watch a directory for changes and auto-scan for vulnerabilities."""
    console.print(BANNER)
    from aether.engine.watcher import AetherWatcher

    config = load_aether_config()
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("api_key")
    model = config.get("model")

    watcher = AetherWatcher(
        target_path=path,
        api_key=api_key,
        model=model,
        debounce_seconds=debounce,
    )
    watcher.start()


@app.command()
def redscan(
    path: str = typer.Argument(".", help="Path to enumerate attack surface"),
):
    """🔴 Run Red Team attack surface enumeration on the target path."""
    console.print(BANNER)

    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[bold red]❌ Path does not exist: {path}[/bold red]")
        raise typer.Exit(code=1)

    from aether.agents.red_attacker import RedTeamAttacker

    attacker = RedTeamAttacker()
    report = attacker.enumerate_attack_surface(str(target))

    if report.vectors:
        console.print(f"\n[bold red]⚠️  {len(report.vectors)} attack vector(s) found.[/bold red]")
    else:
        console.print("\n[bold green]✅ No attack vectors found. Attack surface is minimal.[/bold green]")


@app.command()
def quota():
    """💰 Show API token usage and remaining budget."""
    console.print(BANNER)
    from aether.engine.quota import QuotaEngine
    from rich.table import Table
    from rich import box
    
    stats = QuotaEngine.get_stats()
    
    table = Table(title="💰 Global Quota Engine", box=box.ROUNDED, border_style="green")
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="bold yellow", justify="right")
    
    table.add_row("Total Tokens Used", f"{stats['tokens']:,}")
    table.add_row("Estimated Spend", f"${stats['cost']:.4f}")
    table.add_row("Budget Limit", f"${stats['limit']:.2f}")
    
    console.print(table)
    
    if stats['exceeded']:
        console.print("\n[bold red]⚠️ BUDGET LIMIT EXCEEDED. Agent operations are suspended.[/bold red]")
    else:
        remaining = stats['limit'] - stats['cost']
        console.print(f"\n[bold green]✅ Remaining budget: ${remaining:.4f}[/bold green]")


@app.command()
def plugins():
    """🔌 List and manage loaded plugins."""
    console.print(BANNER)

    from aether.engine.plugins import PluginManager

    manager = PluginManager()
    manager.discover_and_load()
    manager.list_plugins()


if __name__ == "__main__":
    app()

