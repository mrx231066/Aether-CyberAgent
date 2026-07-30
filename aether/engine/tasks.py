"""Foreground/Background Task Orchestration Engine for Aether-CyberAgent v2.0.0"""

import uuid
import threading
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Callable
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
    """Hardened Background Task Orchestrator (v3.0.0)."""
    
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="AetherWorker")
    _futures: Dict[str, concurrent.futures.Future] = {}

    @classmethod
    def submit_task(cls, name: str, func: Callable, *args, **kwargs) -> str:
        task_id = f"TASK-{uuid.uuid4().hex[:8]}"
        
        # Persist task start state atomically
        conn = AetherDB.get_conn()
        conn.execute("INSERT INTO tasks (task_id, status) VALUES (?, ?)", (task_id, "RUNNING"))
        conn.commit()

        # Wrap the function to handle status updates natively
        def _task_wrapper():
            try:
                result = func(*args, **kwargs)
                conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("COMPLETED", task_id))
                conn.commit()
                EventBus.emit("task_completed", {"task_id": task_id, "result": result})
                return result
            except Exception as e:
                conn.execute("UPDATE tasks SET status = ?, error_state = ? WHERE task_id = ?", ("FAILED", str(e), task_id))
                conn.commit()
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
            
        if future.cancel():
            conn = AetherDB.get_conn()
            conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", ("CANCELLED", task_id))
            conn.commit()
            EventBus.emit("task_cancelled", {"task_id": task_id})
            return True
        return False

    @classmethod
    def list_tasks(cls):
        """Fetches persistent task state from the database."""
        conn = AetherDB.get_conn()
        cursor = conn.execute("SELECT task_id, status, error_state, created_at FROM tasks ORDER BY created_at DESC LIMIT 20")
        
        print("\n╭─────────────────────────────────────────────╮")
        print("│              AETHER TASKS (DB)              │")
        print("├─────────────────────────────────────────────┤")
        for row in cursor.fetchall():
            tid, status, err, created = row
            err_disp = f" ({err[:20]}...)" if err else ""
            print(f"│ {tid:<12} | {status:<10} | {created[11:19]} {err_disp}")
        print("╰─────────────────────────────────────────────╯\n")
