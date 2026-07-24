"""Phase 4 & 8: Session Time-Travel & Sliding Context."""
from aether.config import SessionState
from rich.console import Console
import copy

console = Console()

class SessionManager:
    _history_snapshots = {}

    @classmethod
    def prune_context(cls):
        """Phase 4: Sliding Window Context Pruning."""
        if len(SessionState.chat_history) > 10:
            console.print("[dim]• Context limit approaching. Compressing memory...[/dim]")
            mid = len(SessionState.chat_history) // 2
            SessionState.chat_history = ["[State Memory] Summarized previous conversation context."] + SessionState.chat_history[mid:]

    @classmethod
    def rollback(cls, n: int):
        """Phase 8: Rollback n turns."""
        if n >= len(SessionState.chat_history):
            SessionState.chat_history.clear()
        else:
            SessionState.chat_history = SessionState.chat_history[:-n]
        console.print(f"[bold yellow]⏪ Rolled back {n} interactions.[/bold yellow]")

    @classmethod
    def branch(cls, name: str):
        """Phase 8: Fork the session history."""
        cls._history_snapshots[name] = copy.deepcopy(SessionState.chat_history)
        console.print(f"[bold green]🌿 Branched session into: {name}[/bold green]")
        
    @classmethod
    def switch_branch(cls, name: str):
        if name in cls._history_snapshots:
            SessionState.chat_history = copy.deepcopy(cls._history_snapshots[name])
            console.print(f"[bold green]🌿 Switched to branch: {name}[/bold green]")
        else:
            console.print(f"[bold red]❌ Branch not found: {name}[/bold red]")
