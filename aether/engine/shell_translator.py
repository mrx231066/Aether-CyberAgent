"""Phase 3: NL-to-Shell Translation module."""
from aether.config import Config
from rich.console import Console
from rich.prompt import Confirm
import subprocess

console = Console()

def translate_nl_to_shell(nl_query: str) -> str:
    """Detects simple OS tasks in natural language and proposes a shell command."""
    from aether.auth import load_config
    import google.genai as genai
    
    if nl_query.startswith("/") or len(nl_query.split()) < 2:
        return None
        
    os_keywords = ["kill port", "find file", "search for", "list dir", "tail log", "chmod", "chown", "create folder", "delete file", "tar", "unzip"]
    if not any(kw in nl_query.lower() for kw in os_keywords):
        return None
        
    config = load_config()
    api_key = config.get("api_key")
    if not api_key:
        return None
        
    try:
        console.print("[bold yellow]●[/bold yellow] [dim]Analyzing OS intent...[/dim]")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.get("model", "gemini-2.5-flash"),
            contents=f"Convert this natural language to a secure bash command for Linux. Output ONLY the raw command, no backticks, no markdown. Query: {nl_query}"
        )
        cmd = response.text.strip().strip("`")
        
        from rich.panel import Panel
        console.print(f"\n[bold yellow]💡 NL-to-Shell Translation[/bold yellow]")
        console.print(Panel(f"[bold cyan]{cmd}[/bold cyan]", title="Proposed Command", border_style="cyan"))
        
        if Config.GOD_MODE or Confirm.ask("[bold green]Execute this command?[/bold green]", default=True):
            console.print(f"[bold yellow]●[/bold yellow] [dim]bash: {cmd}[/dim]")
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                console.print(f"[bold green]●[/bold green] [dim green]bash success (code 0)[/dim green]")
            else:
                console.print(f"[bold red]●[/bold red] [dim red]bash failed (code {res.returncode})[/dim red]")
            if res.stdout:
                console.print(Panel(res.stdout.strip(), title="stdout", border_style="green"))
            if res.stderr:
                console.print(Panel(res.stderr.strip(), title="stderr", border_style="red"))
            return ""  # Handled
    except Exception as e:
        console.print(f"[bold red]●[/bold red] [dim red]Translation error: {e}[/dim red]")
        
    return None
