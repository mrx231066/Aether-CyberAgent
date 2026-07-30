"""Event Bus for decoupled UI/Backend communication (v4.0.0)."""

from typing import Callable, Dict, List, Any

class EventBus:
    """Synchronous event publisher/subscriber."""
    
    _listeners: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: str, callback: Callable):
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(callback)

    @classmethod
    def emit(cls, event_type: str, payload: dict = None):
        if payload is None:
            payload = {}
        for callback in cls._listeners.get(event_type, []):
            try:
                callback(payload)
            except Exception:
                pass # Prevent one bad listener from crashing the bus
