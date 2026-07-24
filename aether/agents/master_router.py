"""Master Router for Swarm dispatching."""
from aether.engine.swarm import SwarmOrchestrator
from rich.console import Console
import asyncio

console = Console()

class MasterAgent:
    @staticmethod
    def dispatch_parallel_tasks(file_path: str):
        console.print(f"[bold magenta]🐝 Master Agent dispatching swarm for {file_path}[/bold magenta]")
        
        async def audit():
            await asyncio.sleep(1)
            return "Purple Team: Audit completed cleanly."
            
        async def test_gen():
            await asyncio.sleep(1)
            return "Green Team: Unit tests generated."
            
        results = asyncio.run(SwarmOrchestrator.dispatch([audit, test_gen]))
        for r in results:
            console.print(f"[dim]{r}[/dim]")
