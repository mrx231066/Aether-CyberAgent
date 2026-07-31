"""Unit tests for live model discovery, schema parsing, in-memory caching, and error handling across all Aether providers."""

import pytest
from unittest.mock import MagicMock
from aether.ai.providers.helpers import parse_openai_style_models, clear_model_cache
from aether.ai.providers.openai_provider import OpenAIAdapter
from aether.ai.providers.anthropic_provider import AnthropicAdapter
from aether.ai.providers.google_gemini import GoogleGeminiAdapter
from aether.ai.providers.openai_compatible import (
    OpenAICompatibleAdapter, create_openrouter_adapter, create_moonshot_adapter, create_zai_adapter
)
from aether.ai.providers.ollama_provider import OllamaAdapter
from aether.engine.credentials import CredentialManager


def test_parse_openai_style_models():
    mock_data = {
        "data": [
            {"id": "gpt-4o-2026", "name": "GPT-4o 2026", "context_length": 128000},
            {"id": "o3-mini-test", "name": "o3-mini Test", "context_length": 200000},
        ]
    }
    parsed = parse_openai_style_models(mock_data, "openai", "OpenAI")
    assert len(parsed) == 2
    assert parsed[0].model_id == "gpt-4o-2026"
    assert parsed[1].model_id == "o3-mini-test"


def test_openai_live_model_discovery(monkeypatch):
    clear_model_cache("openai")
    adapter = OpenAIAdapter()
    
    mock_client = MagicMock()
    mock_model_1 = MagicMock(id="gpt-4o")
    mock_model_2 = MagicMock(id="o1-preview")
    mock_client.models.list.return_value = MagicMock(data=[mock_model_1, mock_model_2])
    
    adapter._client = mock_client
    monkeypatch.setattr(adapter, "_init_client", lambda: None)
    
    models = adapter.list_models(force_refresh=True)
    assert len(models) == 2
    model_ids = [m.model_id for m in models]
    assert "gpt-4o" in model_ids
    assert "o1-preview" in model_ids


def test_anthropic_live_model_discovery(monkeypatch):
    clear_model_cache("anthropic")
    adapter = AnthropicAdapter()
    
    mock_client = MagicMock()
    mock_m1 = MagicMock(id="claude-3-7-sonnet", display_name="Claude 3.7 Sonnet")
    mock_client.models.list.return_value = MagicMock(data=[mock_m1])
    
    adapter._client = mock_client
    monkeypatch.setattr(adapter, "_init_client", lambda: None)
    
    models = adapter.list_models(force_refresh=True)
    assert len(models) == 1
    assert models[0].model_id == "claude-3-7-sonnet"
    assert models[0].display_name == "Claude 3.7 Sonnet"


def test_gemini_live_model_discovery(monkeypatch):
    clear_model_cache("google_gemini")
    adapter = GoogleGeminiAdapter()
    
    mock_client = MagicMock()
    class MockGeminiModel:
        name = "models/gemini-2.5-pro"
        display_name = "Gemini 2.5 Pro"
        
    mock_client.models.list.return_value = [MockGeminiModel()]
    adapter._client = mock_client
    monkeypatch.setattr(adapter, "_init_client", lambda: None)
    
    models = adapter.list_models(force_refresh=True)
    assert len(models) == 1
    assert models[0].model_id == "gemini-2.5-pro"


def test_openrouter_live_model_discovery(monkeypatch):
    clear_model_cache("openrouter")
    adapter = create_openrouter_adapter()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"}
        ]
    }
    
    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: mock_resp)
    adapter._client = MagicMock()
    monkeypatch.setattr(adapter, "_init_client", lambda: None)
    
    models = adapter.list_models(force_refresh=True)
    assert len(models) == 2
    ids = [m.model_id for m in models]
    assert "openai/gpt-4o" in ids
    assert "anthropic/claude-3.5-sonnet" in ids


def test_ollama_live_model_discovery(monkeypatch):
    clear_model_cache("ollama")
    adapter = OllamaAdapter()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [
            {"name": "llama3:latest"},
            {"name": "codellama:7b"}
        ]
    }
    
    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: mock_resp)
    
    models = adapter.list_models(force_refresh=True)
    assert len(models) == 2
    ids = [m.model_id for m in models]
    assert "llama3:latest" in ids
    assert "codellama:7b" in ids


def test_unauthenticated_fetch_failure_raises_error(monkeypatch):
    clear_model_cache("openai")
    adapter = OpenAIAdapter()
    monkeypatch.setattr(CredentialManager, "get_credential", lambda *args: None)
    adapter._client = None
    
    with pytest.raises(RuntimeError) as exc_info:
        adapter.list_models(force_refresh=True)
    assert "not authenticated" in str(exc_info.value).lower()
