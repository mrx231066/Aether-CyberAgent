"""Transactional SQLite Database Engine for Aether (v4.0.1)."""

import sqlite3
import threading
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class AetherDB:
    """Manages thread-safe SQLite connections, transactions, and schema migrations."""
    
    _local = threading.local()
    
    @classmethod
    def get_conn(cls) -> sqlite3.Connection:
        if not hasattr(cls._local, "conn") or cls._local.conn is None:
            db_dir = Path.home() / ".aether"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "aether.db"
            
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            cls._init_schema(conn)
            cls._local.conn = conn
            
        return cls._local.conn

    @staticmethod
    def _init_schema(conn: sqlite3.Connection):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                prompt TEXT,
                provider TEXT,
                model TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                run_id TEXT,
                status TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                error_state TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS plans (
                plan_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

    @classmethod
    def save_history_entry(cls, session_id: str, role: str, content: str, provider: str = "", model: str = ""):
        """Persist a conversation turn to SQLite."""
        try:
            conn = cls.get_conn()
            conn.execute(
                "INSERT INTO session_history (session_id, role, content, provider, model) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, provider, model)
            )
            conn.commit()
        except Exception:
            pass

    @classmethod
    def get_history(cls, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent session history."""
        try:
            conn = cls.get_conn()
            cursor = conn.execute(
                "SELECT role, content, provider, model, timestamp FROM session_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1], "provider": r[2], "model": r[3], "timestamp": r[4]} for r in reversed(rows)]
        except Exception:
            return []

    @classmethod
    def clear_history(cls, session_id: str = "default") -> bool:
        """Clear conversation history for a session."""
        try:
            conn = cls.get_conn()
            conn.execute("DELETE FROM session_history WHERE session_id = ?", (session_id,))
            conn.commit()
            return True
        except Exception:
            return False

    @classmethod
    def check_integrity(cls) -> Dict[str, Any]:
        """Check database integrity."""
        try:
            conn = cls.get_conn()
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            return {"status": "OK" if result == "ok" else "CORRUPTED", "details": result}
        except Exception as e:
            return {"status": "ERROR", "details": str(e)}

    @classmethod
    def backup(cls, destination: Optional[str] = None) -> str:
        """Create a backup of the SQLite database."""
        db_path = Path.home() / ".aether" / "aether.db"
        if not db_path.exists():
            return "No database to backup."
        
        backup_dir = Path(destination) if destination else Path.home() / ".aether" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"aether_backup_{Path(db_path).stat().st_mtime:.0f}.db"
        
        shutil.copy2(db_path, backup_file)
        return str(backup_file)

    @classmethod
    def repair(cls) -> bool:
        """Attempt SQLite database repair via VACUUM & REINDEX."""
        try:
            conn = cls.get_conn()
            conn.execute("VACUUM")
            conn.execute("REINDEX")
            conn.commit()
            return True
        except Exception:
            return False
