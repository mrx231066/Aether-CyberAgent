"""Centralized Error Taxonomy for Aether (v3.0.0)."""

class AetherError(Exception):
    """Base exception for all Aether operations."""
    def __init__(self, message: str, code: str = "ERR_GENERIC"):
        super().__init__(message)
        self.code = code
        self.message = message

class ConfigurationError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_CONFIG")

class AuthenticationError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_AUTH")

class AuthorizationError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_UNAUTHORIZED")

class ProviderError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_PROVIDER")

class PolicyViolationError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_POLICY")

class SandboxError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_SANDBOX")

class TaskExecutionError(AetherError):
    def __init__(self, message: str):
        super().__init__(message, "ERR_TASK")
