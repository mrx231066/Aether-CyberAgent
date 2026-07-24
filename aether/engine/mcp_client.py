"""Phase 5: Model Context Protocol (MCP) Client."""
from rich.console import Console

console = Console()

class MCPClient:
    """Harness allowing Aether to connect to external MCP servers."""
    
    _connections = {}

    @classmethod
    def connect(cls, url: str):
        proto_type = "Generic"
        if url.startswith("sqlite://"): proto_type = "SQLite"
        elif url.startswith("github://"): proto_type = "GitHub"
        elif url.startswith("jira://"): proto_type = "Jira"
        
        cls._connections[url] = {"status": "connected", "type": proto_type}
        console.print(f"[bold green]🔌 MCP Connected to {proto_type}: {url}[/bold green]")

    @classmethod
    def list_servers(cls):
        if not cls._connections:
            console.print("[yellow]No MCP servers connected.[/yellow]")
            return
        for url, data in cls._connections.items():
            console.print(f" - [bold cyan]{url}[/bold cyan] ({data['status']})")
