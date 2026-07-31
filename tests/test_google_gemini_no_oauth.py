"""Automated regression test proving complete removal of OAuth URL generation in GoogleGeminiAdapter."""

import io
import sys
import socket
from unittest.mock import patch
from aether.ai.providers.google_gemini import GoogleGeminiAdapter
from aether.engine.credentials import CredentialManager

def test_no_oauth_url_printed_for_gemini(monkeypatch):
    CredentialManager.clear_credential("google_gemini")
    adapter = GoogleGeminiAdapter()
    
    # Capture stdout
    stdout_capture = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout_capture)
    
    # Mock user pressing enter (empty key) to prompt
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda prompt, password=False: "")
    
    # Track any socket bindings
    socket_bound = False
    original_bind = socket.socket.bind
    
    def mock_bind(self, address):
        nonlocal socket_bound
        socket_bound = True
        return original_bind(self, address)
        
    monkeypatch.setattr(socket.socket, "bind", mock_bind)
    
    # Execute authentication
    res = adapter.authenticate()
    
    output_text = stdout_capture.getvalue()
    
    # Assertions
    assert "accounts.google.com" not in output_text
    assert "code_challenge" not in output_text
    assert "redirect_uri" not in output_text
    assert "localhost" not in output_text
    assert socket_bound is False
    assert res is False
