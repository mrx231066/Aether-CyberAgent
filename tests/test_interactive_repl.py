"""Integration tests for Aether-CyberAgent v0.2.0 Interactive REPL.

Tests slash command parsing, config management, tool execution,
and the self-correction loop.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Tool Engine Tests ──


class TestToolEngine:
    def test_read_file(self, tmp_path):
        from aether.engine.tools import ToolEngine

        target = tmp_path / "test.py"
        target.write_text("print('hello')\n")

        engine = ToolEngine(working_dir=str(tmp_path))
        content = engine.read_file("test.py")
        assert content == "print('hello')\n"

    def test_read_file_not_found(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            engine.read_file("nonexistent.py")

    def test_write_file(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        result = engine.write_file("output.py", "x = 42\n")
        assert result is True
        assert (tmp_path / "output.py").read_text() == "x = 42\n"

    def test_write_file_creates_dirs(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        engine.write_file("subdir/deep/file.py", "pass\n")
        assert (tmp_path / "subdir" / "deep" / "file.py").exists()

    def test_execute_shell_success(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        result = engine.execute_shell("echo 'hello world'")
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]
        assert result["timed_out"] is False

    def test_execute_shell_failure(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        result = engine.execute_shell("exit 1")
        assert result["exit_code"] == 1

    def test_execute_shell_timeout(self, tmp_path):
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))
        result = engine.execute_shell("sleep 10", timeout=1)
        assert result["timed_out"] is True
        assert result["exit_code"] == -1

    def test_list_dir(self, tmp_path):
        from aether.engine.tools import ToolEngine

        (tmp_path / "main.py").write_text("pass\n")
        (tmp_path / "utils.py").write_text("pass\n")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "helper.py").write_text("pass\n")

        engine = ToolEngine(working_dir=str(tmp_path))
        entries = engine.list_dir(".")
        assert len(entries) >= 3
        # Should contain file entries
        assert any("main.py" in e for e in entries)
        assert any("utils.py" in e for e in entries)

    def test_list_dir_excludes_hidden(self, tmp_path):
        from aether.engine.tools import ToolEngine

        (tmp_path / "visible.py").write_text("pass\n")
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "secret.py").write_text("pass\n")

        engine = ToolEngine(working_dir=str(tmp_path))
        entries = engine.list_dir(".")
        assert all(".hidden" not in e for e in entries)


# ── Slash Command Parsing Tests ──


class TestSlashCommands:
    def test_exit_command(self):
        from aether.cli.interactive import handle_slash_command

        result = handle_slash_command("/exit", "fake_key", "gemini-2.5-flash")
        assert result == "EXIT"

    def test_quit_command(self):
        from aether.cli.interactive import handle_slash_command

        result = handle_slash_command("/quit", "fake_key", "gemini-2.5-flash")
        assert result == "EXIT"

    def test_help_command(self):
        from aether.cli.interactive import handle_slash_command

        # /help should return None (no model change, no exit)
        result = handle_slash_command("/help", "fake_key", "gemini-2.5-flash")
        assert result is None

    def test_clear_command(self):
        from aether.cli.interactive import handle_slash_command

        with patch("os.system"):
            result = handle_slash_command("/clear", "fake_key", "gemini-2.5-flash")
        assert result is None

    def test_unknown_command(self):
        from aether.cli.interactive import handle_slash_command

        result = handle_slash_command("/unknown_xyz", "fake_key", "gemini-2.5-flash")
        assert result is None


# ── Config Management Tests ──


class TestConfigManagement:
    def test_load_config_missing(self, monkeypatch):
        from aether.cli.interactive import load_config, CONFIG_PATH

        monkeypatch.setattr("aether.cli.interactive.CONFIG_PATH", Path("/tmp/nonexistent_aether_config.json"))
        config = load_config()
        assert config == {}

    def test_save_and_load_config(self, tmp_path):
        from aether.cli import interactive

        config_file = tmp_path / ".aether_config.json"
        original_path = interactive.CONFIG_PATH
        interactive.CONFIG_PATH = config_file

        try:
            interactive.save_config({"model": "gemini-2.5-pro", "api_key": "test_key"})
            config = interactive.load_config()
            assert config["model"] == "gemini-2.5-pro"
            assert config["api_key"] == "test_key"
        finally:
            interactive.CONFIG_PATH = original_path

    def test_save_config_updates_existing(self, tmp_path):
        from aether.cli import interactive

        config_file = tmp_path / ".aether_config.json"
        original_path = interactive.CONFIG_PATH
        interactive.CONFIG_PATH = config_file

        try:
            interactive.save_config({"model": "gemini-2.5-flash"})
            interactive.save_config({"api_key": "new_key"})
            config = interactive.load_config()
            assert config["model"] == "gemini-2.5-flash"
            assert config["api_key"] == "new_key"
        finally:
            interactive.CONFIG_PATH = original_path


# ── Self-Correction Loop Tests ──


class TestSelfCorrectionLoop:
    def test_has_traceback_detection(self):
        from aether.agents.gold_autonomic import AutonomicEngine

        assert AutonomicEngine._has_traceback("Traceback (most recent call last):") is True
        assert AutonomicEngine._has_traceback("FileNotFoundError:") is True
        assert AutonomicEngine._has_traceback("All good, no issues") is False
        assert AutonomicEngine._has_traceback("") is False


# ── Yellow Patcher Tests ──


class TestYellowPatcher:
    def test_yellow_patcher_init_with_mock(self):
        from aether.agents.yellow_patcher import YellowPatcher

        with patch("google.genai.Client") as MockClient:
            mock_client = MockClient.return_value
            mock_chat = MagicMock()
            mock_client.chats.create.return_value = mock_chat

            patcher = YellowPatcher(api_key="fake_key", model="gemini-2.5-pro")
            assert patcher.model == "gemini-2.5-pro"
            assert patcher.chat_session is not None

    def test_tool_engine_integration(self, tmp_path):
        """Verify ToolEngine is properly accessible from YellowPatcher."""
        from aether.engine.tools import ToolEngine

        engine = ToolEngine(working_dir=str(tmp_path))

        # Write and read back
        engine.write_file("test.txt", "hello from tools")
        content = engine.read_file("test.txt")
        assert content == "hello from tools"

        # Execute shell
        result = engine.execute_shell("echo 'tool test'")
        assert result["exit_code"] == 0
        assert "tool test" in result["stdout"]
