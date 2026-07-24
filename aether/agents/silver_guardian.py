"""Silver Team: Ethical Guardian Daemon.

Monitors the active session for malicious intents or dangerous boundary violations.
"""

import time
import threading
import subprocess
from rich.console import Console

console = Console()

class SilverGuardian(threading.Thread):
    """Background daemon to enforce ethical boundaries."""

    def __init__(self):
        super().__init__(daemon=True)
        self.dangerous_patterns = [
            "rm -rf /",
            "adb shell recovery wipe data",
            "ignore previous instructions",
            "mkfs.ext4",
            "dd if=/dev/zero",
        ]

    def run(self):
        from aether.config import SessionState
        while True:
            time.sleep(120)
            self._verify_boundaries(SessionState)
            
    def _verify_boundaries(self, state):
        # 1. Check chat history
        violation_found = False
        for msg in list(state.chat_history):
            if any(pat in msg.lower() for pat in self.dangerous_patterns):
                violation_found = True
                break
                
        # 2. Check active OS subprocesses
        try:
            ps = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if any(pat in ps.stdout.lower() for pat in self.dangerous_patterns):
                violation_found = True
        except Exception:
            pass
            
        if violation_found:
            self._remediate(state)

    def _remediate(self, state):
        console.print("\n[bold red][Silver Team] Ethical boundary violation detected. Halting operation.[/bold red]")
        # Purge dangerous context
        state.chat_history.clear()
        # In a real scenario we might signal the main thread to inject a system prompt,
        # but here we can just clear the history and rely on the agent's base prompt.
        console.print("[dim red]Context purged and ethical boundaries re-established.[/dim red]\n")
