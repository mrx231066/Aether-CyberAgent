"""Secure Credential Storage Engine for Aether-CyberAgent."""

import os
from pathlib import Path
from rich.console import Console

console = Console()

class CredentialManager:
    """Manages API keys using OS keyring, falling back to cryptography."""
    
    SERVICE_NAME = "aether_cyberagent"
    FALLBACK_FILE = Path.home() / ".aether" / "encrypted_creds.bin"

    @classmethod
    def save_api_key(cls, key: str, passphrase: str = None) -> bool:
        try:
            import keyring
            keyring.set_password(cls.SERVICE_NAME, "gemini_api_key", key)
            return True
        except Exception:
            return cls._save_fallback(key, passphrase)

    @classmethod
    def get_api_key(cls, passphrase: str = None) -> str | None:
        try:
            import keyring
            key = keyring.get_password(cls.SERVICE_NAME, "gemini_api_key")
            if key:
                return key
        except Exception:
            pass
        return cls._get_fallback(passphrase)

    @classmethod
    def clear_api_key(cls) -> bool:
        success = False
        try:
            import keyring
            keyring.delete_password(cls.SERVICE_NAME, "gemini_api_key")
            success = True
        except Exception:
            pass
            
        if cls.FALLBACK_FILE.exists():
            cls.FALLBACK_FILE.unlink()
            success = True
            
        return success

    @classmethod
    def _save_fallback(cls, key: str, passphrase: str) -> bool:
        console.print("[yellow]⚠️ OS Keyring unavailable. Falling back to encrypted file storage.[/yellow]")
        if not passphrase:
            console.print("[red]❌ Passphrase required for fallback storage.[/red]")
            return False
            
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64

            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'aether_static_salt_123',
                iterations=100000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
            f = Fernet(encryption_key)
            encrypted_data = f.encrypt(key.encode())
            
            cls.FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
            cls.FALLBACK_FILE.write_bytes(encrypted_data)
            return True
        except ImportError:
            console.print("[bold red]❌ 'cryptography' library not installed. Cannot securely store keys without keyring.[/bold red]")
            return False

    @classmethod
    def _get_fallback(cls, passphrase: str) -> str | None:
        if not cls.FALLBACK_FILE.exists() or not passphrase:
            return None
            
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'aether_static_salt_123',
                iterations=100000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
            f = Fernet(encryption_key)
            return f.decrypt(cls.FALLBACK_FILE.read_bytes()).decode()
        except Exception:
            return None
