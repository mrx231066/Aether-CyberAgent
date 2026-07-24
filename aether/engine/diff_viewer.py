"""Phase 7: Git-Style Diff Rendering."""
from rich.console import Console
from rich.text import Text
import difflib

console = Console()

class DiffViewer:
    @classmethod
    def render_diff(cls, original: str, proposed: str, filename: str):
        console.print(f"\n[bold yellow]📝 Proposed changes for {filename}:[/bold yellow]")
        
        diff = difflib.unified_diff(
            original.splitlines(),
            proposed.splitlines(),
            fromfile=filename,
            tofile=filename,
            lineterm=""
        )
        
        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                console.print(Text(line, style="green"))
            elif line.startswith("-") and not line.startswith("---"):
                console.print(Text(line, style="red"))
            elif line.startswith("@@"):
                console.print(Text(line, style="cyan"))
            else:
                console.print(line)
        console.print()
