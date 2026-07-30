"""Transactional SQLite Database Engine for Aether (v4.0.0)."""

import sqlite3
import threading
from pathlib import Path

class AetherDB:
    """Manages thread-safe SQLite connections and schema."""
    
    _local = threading.local()
    
    @classmethod
    def get_conn(cls) -> sqlite3.Connection:
        if not hasattr(cls._local, "conn"):
            db_dir = Path.home() / ".aether"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "aether.db"
            
            # WAL mode for high-concurrency background task writes
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
        """)
        conn.commit()
