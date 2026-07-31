"""Global configuration state for Aether-CyberAgent v4.0.1."""
from typing import List, Dict, Any, Optional

class Config:
    """Global configuration state."""
    GOD_MODE = False
    OFFLINE_MODE = False
    WATCH_MODE = False

class SessionState:
    """Manages active session context and configuration.
    Uses class-level attributes to support both static and instance access without AttributeError.
    """
    project_root: str = "."
    auto_apply_patches: bool = False
    verbose_tools: bool = False
    max_retries: int = 3
    yolo_mode: bool = False       # YOLO MODE toggle
    local_only: bool = False      # Local-First Privacy toggle
    total_tokens: int = 0
    start_time: str = ""
    capabilities: Any = None      # Injected at startup
    history: List[Dict[str, Any]] = []
    chat_history: List[Any] = []
    current_plan: Optional[Dict[str, Any]] = None
