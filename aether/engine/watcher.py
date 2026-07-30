"""Watch Mode for Aether-CyberAgent v4.0.0.

Continuous file monitoring with automatic security scanning
on file changes using watchdog.
"""

import time
from pathlib import Path
from typing import Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()


class AetherWatcher:
    """Watches a directory for file changes and triggers security scans.

    Uses watchdog to monitor filesystem events and automatically runs
    Blue Team analysis on modified Python files.
    """

    def __init__(
        self,
        target_path: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        debounce_seconds: float = 2.0,
    ) -> None:
        self.target_path = Path(target_path).resolve()
        self.api_key = api_key
        self.model = model
        self.debounce_seconds = debounce_seconds
        self._pending_files: Set[str] = set()
        self._last_event_time: float = 0.0

    def start(self) -> None:
        """Start watching the target directory."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
        except ImportError:
            console.print("[bold red]❌ watchdog not installed. Run: pip install watchdog[/bold red]")
            return

        watcher = self

        class AetherHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".py"):
                    watcher._on_file_changed(event.src_path)

            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith(".py"):
                    watcher._on_file_changed(event.src_path)

        observer = Observer()
        handler = AetherHandler()
        observer.schedule(handler, str(self.target_path), recursive=True)

        console.print(Panel(
            f"[bold white]Target:[/bold white] {self.target_path}\n"
            f"[bold white]Debounce:[/bold white] {self.debounce_seconds}s\n"
            f"[bold white]Status:[/bold white] [green]Watching...[/green]\n\n"
            "[dim]Press Ctrl+C to stop[/dim]",
            title="🔄 Aether Watch Mode",
            border_style="cyan",
            box=box.ROUNDED,
        ))

        observer.start()
        try:
            while True:
                time.sleep(0.5)
                self._process_pending()
        except KeyboardInterrupt:
            console.print("\n[bold cyan]⏹️  Watch mode stopped.[/bold cyan]")
            observer.stop()
        observer.join()

    def _on_file_changed(self, file_path: str) -> None:
        """Handle a file change event with debouncing."""
        # Skip hidden dirs and common noise
        skip_patterns = {"__pycache__", ".venv", "venv", ".git", ".aether", "node_modules"}
        if any(pat in file_path for pat in skip_patterns):
            return

        self._pending_files.add(file_path)
        self._last_event_time = time.time()

    def _process_pending(self) -> None:
        """Process pending file changes after debounce period."""
        if not self._pending_files:
            return

        elapsed = time.time() - self._last_event_time
        if elapsed < self.debounce_seconds:
            return

        files = list(self._pending_files)
        self._pending_files.clear()

        console.print(f"\n[bold yellow]📂 {len(files)} file(s) changed — running security scan...[/bold yellow]")

        from aether.agents.blue_auditor import BlueTeamAuditor

        auditor = BlueTeamAuditor()
        total_findings = 0

        for file_path in files:
            if not Path(file_path).exists():
                continue

            console.print(f"  [dim]🔍 Scanning: {Path(file_path).name}[/dim]")
            findings = auditor.scan_file(file_path)

            if findings:
                total_findings += len(findings)
                for f in findings:
                    sev_color = {
                        "CRITICAL": "bold red",
                        "HIGH": "red",
                        "MEDIUM": "yellow",
                        "LOW": "green",
                    }.get(f.severity, "white")
                    console.print(
                        f"    [{sev_color}]{f.severity}[/{sev_color}] "
                        f"{f.vulnerability_type} at line {f.line_number}: {f.description}"
                    )

        if total_findings == 0:
            console.print("  [green]✅ No vulnerabilities detected.[/green]")
        else:
            console.print(f"  [yellow]⚠️  {total_findings} vulnerability(ies) found.[/yellow]")

        console.print("[dim]👁️  Watching for changes...[/dim]")
