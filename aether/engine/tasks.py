"""Foreground/Background Task Orchestration Engine for Aether-CyberAgent v4.0.1"""

import uuid
import threading
import time
import concurrent.futures
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, Optional
from rich.console import Console
from rich.table import Table

console = Console()

class TaskState(Enum):
    QUEUED = "QUEUED"
    CLASSIFIED = "CLASSIFIED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"

from aether.engine.db import AetherDB
from aether.engine.events import EventBus
from aether.engine.errors import TaskExecutionError

class TaskEngine:
    """Hardened Background Task Orchestrator (v4.0.1)."""
    
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="AetherWorker")
    _futures: Dict[str, concurrent.futures.Future] = {}
    _task_logs: Dict[str, list] = {}
    _task_meta: Dict[str, dict] = {}

    @classmethod
    def submit_task(cls, name: str, func: Callable, *args, **kwargs) -> str:
        task_id = f"TASK-{uuid.uuid4().hex[:8]}"
        cls._task_logs[task_id] = [f"Task {task_id} ({name}) submitted at {time.strftime('%H:%M:%S')}"]
        cls._task_meta[task_id] = {"name": name, "func": func, "args": args, "kwargs": kwargs}
        
        # Persist task start state atomically
        try:
            conn = AetherDB.get_conn()
            conn.execute("INSERT INTO tasks (task_id, status) VALUES (?, ?)", (task_id, "RUNNING"))
            conn.commit()
        except Exception:
            pass

        def _task_wrapper():
            try:
                cls._task_logs[task_id].append("Execution started.")
                result = func(*args, **kwargs)
                cls._task_logs[task_id].append("Execution completed successfully.")
                try:
                    conn = AetherDB.get_conn()
                    conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("COMPLETED", task_id))
                    conn.commit()
                except Exception:
                    pass
                EventBus.emit("task_completed", {"task_id": task_id, "result": result})
                return result
            except Exception as e:
                cls._task_logs[task_id].append(f"Execution failed: {e}")
                try:
                    conn = AetherDB.get_conn()
                    conn.execute("UPDATE tasks SET status = ?, error_state = ? WHERE task_id = ?", ("FAILED", str(e), task_id))
                    conn.commit()
                except Exception:
                    pass
                EventBus.emit("task_failed", {"task_id": task_id, "error": str(e)})
                raise TaskExecutionError(f"Task {task_id} failed: {e}")

        future = cls._executor.submit(_task_wrapper)
        cls._futures[task_id] = future
        
        EventBus.emit("task_started", {"task_id": task_id, "name": name})
        return task_id

    @classmethod
    def cancel_task(cls, task_id: str) -> bool:
        future = cls._futures.get(task_id)
        if not future:
            return False
            
        cls._task_logs.setdefault(task_id, []).append("Cancellation requested.")
        if future.cancel():
            try:
                conn = AetherDB.get_conn()
                conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("CANCELLED", task_id))
                conn.commit()
            except Exception:
                pass
            EventBus.emit("task_cancelled", {"task_id": task_id})
            return True
        return False

    @classmethod
    def kill_task(cls, task_id: str) -> bool:
        """Alias for cancel_task."""
        return cls.cancel_task(task_id)

    @classmethod
    def pause_task(cls, task_id: str) -> bool:
        cls._task_logs.setdefault(task_id, []).append("Task paused.")
        try:
            conn = AetherDB.get_conn()
            conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("PAUSED", task_id))
            conn.commit()
            return True
        except Exception:
            return False

    @classmethod
    def resume_task(cls, task_id: str) -> bool:
        cls._task_logs.setdefault(task_id, []).append("Task resumed.")
        try:
            conn = AetherDB.get_conn()
            conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("RUNNING", task_id))
            conn.commit()
            return True
        except Exception:
            return False

    @classmethod
    def retry_task(cls, task_id: str) -> Optional[str]:
        meta = cls._task_meta.get(task_id)
        if not meta:
            return None
        return cls.submit_task(f"Retry {meta['name']}", meta['func'], *meta['args'], **meta['kwargs'])

    @classmethod
    def get_logs(cls, task_id: str) -> list:
        return cls._task_logs.get(task_id, ["No logs found for this task ID."])

    @classmethod
    def list_tasks(cls):
        """Fetches persistent task state from the database."""
        try:
            conn = AetherDB.get_conn()
            cursor = conn.execute("SELECT task_id, status, error_state, created_at FROM tasks ORDER BY created_at DESC LIMIT 20")
            rows = cursor.fetchall()
        except Exception:
            rows = []
        
        console.print("\n╭─────────────────────────────────────────────╮")
        console.print("│              [bold cyan]AETHER TASKS (DB)[/bold cyan]              │")
        console.print("├─────────────────────────────────────────────┤")
        if rows:
            for row in rows:
                tid, status, err, created = row
                err_disp = f" ({err[:20]}...)" if err else ""
                created_str = str(created)[11:19] if created else "N/A"
                console.print(f"│ {tid:<14} │ {status:<10} │ {created_str} {err_disp}")
        else:
            console.print("│ [dim yellow]No tasks found in history.[/dim yellow]                │")
        console.print("╰─────────────────────────────────────────────╯\n")
