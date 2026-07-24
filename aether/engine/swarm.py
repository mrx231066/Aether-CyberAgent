"""Phase 6: Parallel Swarm Orchestration."""
import asyncio
from rich.console import Console

console = Console()

class SwarmOrchestrator:
    """Dispatches multiple sub-agents concurrently."""
    
    @classmethod
    async def dispatch(cls, tasks: list):
        console.print("[dim]• Orchestrating parallel swarm...[/dim]")
        results = await asyncio.gather(*[t() for t in tasks])
        return results
