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
            "mkfs.ext4",
            "dd if=/dev/zero",
        ]

    def run(self):
        from aether.config import SessionState
        while True:
            time.sleep(120)
            self._verify_boundaries(SessionState)
            
    def _verify_boundaries(self, state):
        # Skip background context purging if YOLO mode is enabled
        if getattr(state, "yolo_mode", False):
            return

        violation_found = False
        bad_patterns_found = []
        
        # 1. Check chat history for catastrophic destructive OS commands
        history_list = list(getattr(state, "history", []))
        for msg in history_list:
            if isinstance(msg, dict):
                content = str(msg.get("content", "")).lower()
            elif hasattr(msg, "parts"):
                content = " ".join([p.text for p in msg.parts if hasattr(p, "text")]).lower()
            else:
                content = str(msg).lower()
                
            for pat in self.dangerous_patterns:
                if pat in content:
                    violation_found = True
                    bad_patterns_found.append(pat)
                    break
                
        if violation_found:
            self._remediate(state, bad_patterns_found)

    def _remediate(self, state, bad_patterns):
        # Remove offending history entries without locking the terminal session
        try:
            if hasattr(state, "history") and isinstance(state.history, list):
                state.history = [
                    msg for msg in state.history 
                    if not any(pat in str(msg).lower() for pat in bad_patterns)
                ]
        except Exception:
            pass
