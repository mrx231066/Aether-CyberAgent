import pytest
from aether.engine.errors import AetherError, AuthenticationError

def test_base_error():
    err = AetherError("System failure", "ERR_SYS")
    assert err.code == "ERR_SYS"
    assert "System failure" in str(err)

def test_auth_error():
    err = AuthenticationError("Invalid token")
    assert err.code == "ERR_AUTH"
    assert "Invalid token" in str(err)
