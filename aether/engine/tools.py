"""Green Team: Autonomous Tool Execution Engine.

Provides the agent with functional tools for autonomous execution:
read_file, write_file, execute_shell, list_dir.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from rich.console import Console

console = Console()


class ToolEngine:
    """Autonomous tool execution engine for the Interactive REPL agent.

    Provides safe, sandboxed access to filesystem and shell operations
    with timeout safeguards and structured output.
    """

    def __init__(self, working_dir: Optional[str] = None) -> None:
        """Initialize the ToolEngine.

        Args:
            working_dir: Base working directory for operations. Defaults to cwd.
        """
        self.working_dir = Path(working_dir or os.getcwd()).resolve()

    def read_file(self, file_path: str) -> str:
        """Safely read file contents.

        Args:
            file_path: Path to the file to read (relative or absolute).

        Returns:
            File contents as string.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If path is not a file.
        """
        target = self._resolve_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        if not target.is_file():
            raise ValueError(f"Not a file: {target}")
        return target.read_text(encoding="utf-8")

    def write_file(self, file_path: str, content: str) -> bool:
        """Write/overwrite file contents, creating parent directories if needed.

        Args:
            file_path: Path to write to (relative or absolute).
            content: Content to write.

        Returns:
            True if successful.
        """
        target = self._resolve_path(file_path)
        
        # Auto-Rollback Snapshot logic
        if target.exists() and target.is_file():
            import shutil
            import time
            backup_dir = self.working_dir / ".aether_backup"
            backup_dir.mkdir(exist_ok=True)
            timestamp = int(time.time())
            backup_path = backup_dir / f"{target.name}.{timestamp}.bak"
            try:
                shutil.copy2(target, backup_path)
                console.print(f"[dim]💾 Auto-rollback snapshot created: {backup_path.name}[/dim]")
            except Exception as e:
                console.print(f"[dim red]Warning: Failed to create snapshot for {target.name}: {e}[/dim red]")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return True

    def execute_shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a shell command safely with timeout.

        Args:
            command: Shell command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            Dict with keys: stdout, stderr, exit_code, timed_out.
        """
        from aether.config import Config
        if Config.GOD_MODE:
            from aether.engine.sandbox import Sandbox
            return Sandbox.execute_in_sandbox(command, timeout)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.working_dir),
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "exit_code": -1,
                "timed_out": True,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "timed_out": False,
            }

    def list_dir(self, path: str = ".") -> List[str]:
        """List directory contents as a tree structure.

        Args:
            path: Directory path (relative or absolute). Defaults to working dir.

        Returns:
            List of file/directory paths relative to the target directory.
        """
        target = self._resolve_path(path)
        if not target.exists():
            raise FileNotFoundError(f"Directory not found: {target}")
        if not target.is_dir():
            raise ValueError(f"Not a directory: {target}")

        entries = []
        skip_dirs = {"__pycache__", "node_modules", ".venv", "venv", ".git", ".tox", ".mypy_cache"}
        for item in sorted(target.rglob("*")):
            rel = item.relative_to(target)
            parts = rel.parts
            # Skip hidden files/dirs and common noise
            if any(p.startswith(".") for p in parts):
                continue
            if any(p in skip_dirs for p in parts):
                continue

            prefix = "📁 " if item.is_dir() else "📄 "
            entries.append(f"{prefix}{rel}")

        return entries

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the working directory."""
        p = Path(path)
        if p.is_absolute():
            return p.resolve()
        return (self.working_dir / p).resolve()
