"""Synchronous Pre-Execution Command Guard for Aether-CyberAgent.

Intercepts and analyzes shell commands before execution to block destructive operations.
"""

import re
from rich.console import Console
from rich.prompt import Prompt

console = Console()

class CommandGuard:
    """Evaluates commands against a denylist of destructive patterns."""

    # Patterns for known-destructive operations
    _DESTRUCTIVE_PATTERNS = [
        re.compile(r'rm\s+-(?:r|f|rf|fr)\s+(?:/|~|/\w+)'),  # recursive delete of root/home
        re.compile(r':\(\)\{\s*:\|:&\s*\};\(':'),           # bash fork bomb
        re.compile(r'(?:mkfs|fdisk|dd\s+if=/dev/(?:zero|random|urandom)\s+of=/dev/)'), # disk formatting/wiping
        re.compile(r'>\s*/dev/sda'),                        # overriding block devices
        re.compile(r'chmod\s+-R\s+777\s+/'),                # destroying system permissions
        re.compile(r'chown\s+-R\s+root:root\s+/')
    ]

    @classmethod
    def evaluate_and_confirm(cls, cmd_args: list[str] | str) -> bool:
        """
        Evaluates a command. If it matches a destructive pattern, blocks it by default.
        Allows override ONLY via a typed confirmation phrase.
        """
        cmd_str = " ".join(cmd_args) if isinstance(cmd_args, list) else cmd_args
        
        is_destructive = False
        matched_pattern = ""
        
        for pattern in cls._DESTRUCTIVE_PATTERNS:
            if pattern.search(cmd_str):
                is_destructive = True
                matched_pattern = pattern.pattern
                break

        if not is_destructive:
            return True # Command is safe

        console.print(f"\n[bold red]🛑 COMMAND GUARD INTERCEPT: Destructive Pattern Detected[/bold red]")
        console.print(f"[dim]Command: {cmd_str}[/dim]")
        console.print(f"[dim]Matched rule: {matched_pattern}[/dim]")
        console.print("[bold yellow]This operation could severely damage the host system and is blocked by default.[/bold yellow]")
        
        # Hard Confirmation (Typed phrase, not just y/n)
        override_phrase = "I accept the risk"
        user_input = Prompt.ask(f"To override, type strictly: '[bold white]{override_phrase}[/bold white]'")
        
        if user_input.strip() == override_phrase:
            # Audit log the override
            try:
                from aether.engine.quota import AuditLogger
                AuditLogger.log_event("COMMAND_GUARD", "OVERRIDE", f"Destructive command allowed: {cmd_str}")
            except ImportError:
                pass
            return True
            
        console.print("[dim]Command execution blocked.[/dim]")
        return False
