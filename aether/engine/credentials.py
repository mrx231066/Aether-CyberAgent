"""Secure Credential Storage Engine for Aether-CyberAgent.

Supports per-provider credential isolation using OS keyring
with encrypted file fallback.
"""

import os
import json
from pathlib import Path
from rich.console import Console

console = Console()

class CredentialManager:
    """Manages API keys using OS keyring, falling back to encrypted file storage."""
    
    SERVICE_NAME = "aether_cyberagent"
    CRED_DIR = Path.home() / ".aether" / "credentials"

    @classmethod
    def save_credential(cls, provider_id: str, key: str) -> bool:
        """Save a credential for a specific provider."""
        try:
            import keyring
            keyring.set_password(cls.SERVICE_NAME, f"{provider_id}_api_key", key)
            return True
        except Exception:
            return cls._save_file(provider_id, key)

    @classmethod
    def get_credential(cls, provider_id: str) -> str | None:
        """Retrieve a credential for a specific provider."""
        # Check environment variable first
        env_map = {
            "google_gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "zai": "ZAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_var = env_map.get(provider_id)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]

        try:
            import keyring
            key = keyring.get_password(cls.SERVICE_NAME, f"{provider_id}_api_key")
            if key:
                return key
        except Exception:
            pass
        return cls._get_file(provider_id)

    @classmethod
    def clear_credential(cls, provider_id: str) -> bool:
        """Clear a credential for a specific provider."""
        success = False
        try:
            import keyring
            keyring.delete_password(cls.SERVICE_NAME, f"{provider_id}_api_key")
            success = True
        except Exception:
            pass
        
        cred_file = cls.CRED_DIR / f"{provider_id}.key"
        if cred_file.exists():
            cred_file.unlink()
            success = True
        return success

    @classmethod
    def list_stored_providers(cls) -> list:
        """List provider IDs that have stored credentials."""
        providers = []
        # Check file-based credentials
        if cls.CRED_DIR.exists():
            for f in cls.CRED_DIR.glob("*.key"):
                providers.append(f.stem)
        return providers

    # --- Legacy compatibility ---
    @classmethod
    def save_api_key(cls, key: str, passphrase: str = None) -> bool:
        """Legacy: save Gemini API key."""
        return cls.save_credential("google_gemini", key)

    @classmethod
    def get_api_key(cls, passphrase: str = None) -> str | None:
        """Legacy: get Gemini API key."""
        return cls.get_credential("google_gemini")

    @classmethod
    def clear_api_key(cls) -> bool:
        """Legacy: clear Gemini API key."""
        return cls.clear_credential("google_gemini")

    # --- File-based storage (encrypted with machine-bound key) ---
    @classmethod
    def _get_machine_key(cls) -> bytes:
        import socket, getpass, hashlib
        seed = f"{socket.gethostname()}:{getpass.getuser()}:aether_cred_salt"
        return hashlib.sha256(seed.encode()).digest()

    @classmethod
    def _encrypt(cls, text: str) -> str:
        import base64
        key_bytes = cls._get_machine_key()
        data = text.encode('utf-8')
        cipher = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))
        return base64.b64encode(cipher).decode('utf-8')

    @classmethod
    def _decrypt(cls, ciphertext: str) -> str:
        try:
            import base64
            key_bytes = cls._get_machine_key()
            cipher = base64.b64decode(ciphertext.encode('utf-8'))
            data = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(cipher))
            return data.decode('utf-8')
        except Exception:
            return ciphertext

    @classmethod
    def _save_file(cls, provider_id: str, key: str) -> bool:
        """Save encrypted credential to a file with restrictive permissions (0o600)."""
        try:
            cls.CRED_DIR.mkdir(parents=True, exist_ok=True)
            cred_file = cls.CRED_DIR / f"{provider_id}.key"
            encrypted = cls._encrypt(key)
            cred_file.write_text(encrypted)
            cred_file.chmod(0o600)
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to save credential: {e}[/red]")
            return False

    @classmethod
    def _get_file(cls, provider_id: str) -> str | None:
        """Read and decrypt credential from file."""
        cred_file = cls.CRED_DIR / f"{provider_id}.key"
        if cred_file.exists():
            content = cred_file.read_text().strip()
            return cls._decrypt(content)
        return None
