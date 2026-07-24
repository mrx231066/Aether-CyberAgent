"""Nuitka Standalone Binary Build Script for Aether-CyberAgent v1.0.5"""
import subprocess
from rich.console import Console
from pathlib import Path

console = Console()

def build():
    console.print("[bold cyan]🚀 Starting Nuitka C-Compilation Pipeline...[/bold cyan]")
    
    # Ensure dist dir exists
    Path("dist").mkdir(exist_ok=True)
    
    cmd = [
        "python", "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--follow-imports",
        "--enable-plugin=tk-inter",
        "--output-filename=aether",
        "--output-dir=dist",
        "aether/cli/main.py"
    ]
    
    console.print(f"[dim]Executing: {' '.join(cmd)}[/dim]")
    
    try:
        subprocess.run(cmd, check=True)
        console.print("[bold green]✅ Build successful! Binary located at dist/aether[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Build failed: {e}[/bold red]")

if __name__ == "__main__":
    build()
