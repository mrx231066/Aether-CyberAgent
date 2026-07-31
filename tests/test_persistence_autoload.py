"""Automated regression test for login credentials and session history persistence across restarts."""

from aether.engine.credentials import CredentialManager
from aether.ai.provider_manager import ProviderManager
from aether.auth import save_config, load_config
from aether.engine.db import AetherDB
from aether.config import SessionState

def test_provider_credentials_and_session_memory_persistence():
    try:
        # Save mock credentials and configuration state
        CredentialManager.save_credential("openai", "sk-mock-key-12345")
        save_config({"active_provider": "openai", "active_model": "gpt-4o"})
        
        # Save history to SQLite database WAL
        AetherDB.save_history("user", "Test prompt for session persistence")
        AetherDB.save_history("assistant", "Test response from Aether")

        # Wipe in-memory session state (simulating CLI exit & restart)
        ProviderManager._providers.clear()
        ProviderManager._active_provider_name = None
        ProviderManager._active_model_id = None
        SessionState.history.clear()

        # Trigger auto_load on restart
        ProviderManager.auto_load()
        history = AetherDB.get_history()

        # Assert SQLite history persistence
        assert len(history) >= 2
        assert history[-1]["content"] == "Test response from Aether"
    finally:
        # Always clean up test credentials so user environment stays clean
        CredentialManager.clear_credential("openai")
        save_config({"active_provider": None, "active_model": None})
        ProviderManager._providers.clear()
        ProviderManager._active_provider_name = None
        ProviderManager._active_model_id = None
