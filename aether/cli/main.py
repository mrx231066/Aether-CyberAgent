"""Aether-CyberAgent CLI: The command-line interface.

Entry point for the `aether` command. Provides scan, verify, and dashboard
subcommands powered by the full multi-agent pipeline.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box

app = typer.Typer(
    name="aether",
    help="🛡️ Aether-CyberAgent: Autonomous Multi-Agent AI Security Platform",
    add_completion=False,
)
console = Console()

BANNER = """[bold cyan]
   ╔═══════════════════════════════════════════════╗
   ║          🛡️  AETHER-CYBERAGENT  🛡️            ║
   ║   Autonomous Multi-Agent AI Security Platform  ║
   ║              v0.1.0 · Defense Only             ║
   ╚═══════════════════════════════════════════════╝
[/bold cyan]"""


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Aether-CyberAgent: Autonomous AI Security Platform."""
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print(
            Panel(
                "[dim]Run [bold]aether scan <path>[/bold] to start a security audit.\n"
                "Run [bold]aether dashboard[/bold] to launch the live visualizer.\n"
                "Run [bold]aether verify <path>[/bold] to verify a specific file.[/dim]",
                title="🚀 Quick Start",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )


@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to scan for vulnerabilities"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    max_retries: int = typer.Option(3, "--max-retries", "-r", help="Max self-healing retries"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="GEMINI_API_KEY", help="Gemini API key"),
):
    """🔵 Run a full autonomous security scan on the target path."""
    console.print(BANNER)

    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[bold red]❌ Path does not exist: {path}[/bold red]")
        raise typer.Exit(code=1)

    from aether.agents.gold_autonomic import AutonomicEngine
    from aether.reports.sarif import SarifReporter

    try:
        engine = AutonomicEngine(max_retries=max_retries, api_key=api_key)
        result = engine.execute_scan(str(target))

        # Generate SARIF report
        if result.vulnerabilities_found > 0:
            reporter = SarifReporter()
            sarif_path = reporter.export_from_pipeline(result, ".aether/reports")
            console.print(f"\n[bold white]📋 SARIF report saved: {sarif_path}[/bold white]")

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


if __name__ == "__main__":
    app()
