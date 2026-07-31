"""Tests for Aether-CyberAgent v2.0.0 new features.

Tests Red Team agent, plugin system, watch mode, and HTML reports.
"""

import tempfile
from pathlib import Path

import pytest


# ── Red Team Tests ──


VULNERABLE_FLASK_APP = '''
from flask import Flask, request
import sqlite3

app = Flask(__name__)

SECRET_KEY = "sk-proj-abc123xyz456def789ghi012jkl345mno678pqr901"

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")
    conn = sqlite3.connect("app.db")
    conn.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()
    return "deleted"

@app.route("/api/fetch", methods=["GET"])
def fetch_url():
    import requests
    url = request.args.get("url")
    resp = requests.get(url)
    return resp.text

DEBUG = True
'''

CLEAN_CODE = '''
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"
'''


class TestRedTeamAttacker:
    def test_detects_sqli_pattern(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        vuln_file = tmp_path / "app.py"
        vuln_file.write_text(VULNERABLE_FLASK_APP)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        sqli_vectors = [v for v in report.vectors if v.vector_type == "sql_injection"]
        assert len(sqli_vectors) > 0

    def test_detects_entropy_secrets(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        vuln_file = tmp_path / "config.py"
        vuln_file.write_text(VULNERABLE_FLASK_APP)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        secret_vectors = [v for v in report.vectors
                         if v.vector_type in ("hardcoded_secret", "high_entropy_secret")]
        assert len(secret_vectors) > 0

    def test_detects_dangerous_defaults(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        vuln_file = tmp_path / "settings.py"
        vuln_file.write_text(VULNERABLE_FLASK_APP)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        debug_vectors = [v for v in report.vectors if v.vector_type == "dangerous_default"]
        assert len(debug_vectors) > 0

    def test_clean_code_no_vectors(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        safe_file = tmp_path / "safe.py"
        safe_file.write_text(CLEAN_CODE)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        assert len(report.vectors) == 0

    def test_shannon_entropy(self):
        from aether.agents.red_attacker import RedTeamAttacker

        # Random-looking string should have high entropy
        high_entropy = "aK3bM9cN2dP7eQ4fR1gS6hT8iU5jV0kW"
        entropy = RedTeamAttacker._shannon_entropy(high_entropy)
        assert entropy > 4.0

        # Repetitive string should have low entropy
        low_entropy = "aaaaaaaaaa"
        entropy = RedTeamAttacker._shannon_entropy(low_entropy)
        assert entropy < 1.0

    def test_attack_surface_score(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        vuln_file = tmp_path / "app.py"
        vuln_file.write_text(VULNERABLE_FLASK_APP)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        assert report.attack_surface_score >= 0.0
        assert report.attack_surface_score <= 10.0

    def test_generates_recommendations(self, tmp_path):
        from aether.agents.red_attacker import RedTeamAttacker

        vuln_file = tmp_path / "app.py"
        vuln_file.write_text(VULNERABLE_FLASK_APP)

        attacker = RedTeamAttacker()
        report = attacker.enumerate_attack_surface(str(tmp_path))

        assert len(report.recommendations) > 0


# ── Plugin System Tests ──


class TestPluginSystem:
    def test_plugin_manager_singleton(self):
        from aether.engine.plugins import PluginManager

        m1 = PluginManager()
        m2 = PluginManager()
        assert m1 is m2

    def test_register_tool(self):
        from aether.engine.plugins import PluginManager

        manager = PluginManager()
        manager.register_tool("test_tool", lambda: "result")
        assert manager.get_tool("test_tool") is not None

    def test_register_command(self):
        from aether.engine.plugins import PluginManager

        manager = PluginManager()
        manager.register_command("test_cmd", lambda: None)
        assert manager.get_command("test_cmd") is not None

    def test_load_single_file_plugin(self, tmp_path):
        from aether.engine.plugins import PluginManager, PLUGIN_DIR

        # Create a test plugin
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_file.write_text('''
PLUGIN_META = {
    "name": "test_plugin",
    "version": "1.0.0",
    "author": "Test",
    "description": "A test plugin",
    "type": "tool",
}

def register(manager):
    manager.register_tool("test_from_plugin", lambda: "hello")
''')

        import aether.engine.plugins as plugins_mod
        original_dir = plugins_mod.PLUGIN_DIR

        try:
            plugins_mod.PLUGIN_DIR = plugin_dir
            manager = PluginManager.__new__(PluginManager)
            manager._plugins = {}
            manager._tool_hooks = {}
            manager._command_hooks = {}
            manager._scanner_hooks = []
            result = manager._load_single_file_plugin(plugin_file)
            assert result is not None
            assert result.name == "test_plugin"
        finally:
            plugins_mod.PLUGIN_DIR = original_dir


# ── HTML Report Tests ──


class TestHtmlReporter:
    def test_generate_html_report(self):
        from aether.reports.html_report import HtmlReporter
        from aether.agents.gold_autonomic import PipelineResult

        reporter = HtmlReporter()
        result = PipelineResult(
            success=True,
            files_scanned=5,
            vulnerabilities_found=2,
            vulnerabilities_fixed=2,
            verified_patches=[{
                "file": "/tmp/test.py",
                "vulnerability_title": "eval() usage",
                "severity": "CRITICAL",
                "attempts": 1,
                "verification": {"z3": "verified", "hypothesis": "passed"},
            }],
            failed_patches=[],
            scan_duration=1.5,
            state_log=[],
        )

        html = reporter.generate_report(result)
        assert "AETHER-CYBERAGENT" in html
        assert "v4.0.1" in html
        assert "eval() usage" in html

    def test_save_html_report(self, tmp_path):
        from aether.reports.html_report import HtmlReporter
        from aether.agents.gold_autonomic import PipelineResult

        reporter = HtmlReporter()
        result = PipelineResult(
            success=True,
            files_scanned=0,
            vulnerabilities_found=0,
            vulnerabilities_fixed=0,
            verified_patches=[],
            failed_patches=[],
            scan_duration=0.0,
            state_log=[],
        )

        html = reporter.generate_report(result)
        output_dir = str(tmp_path / "reports")
        path = reporter.save_report(html, output_dir)

        assert Path(path).exists()
        assert Path(path).suffix == ".html"


# ── Watch Mode Tests ──


class TestAetherWatcher:
    def test_watcher_init(self, tmp_path):
        from aether.engine.watcher import AetherWatcher

        watcher = AetherWatcher(str(tmp_path))
        assert watcher.target_path == tmp_path.resolve()
        assert watcher.debounce_seconds == 2.0

    def test_watcher_debounce_config(self, tmp_path):
        from aether.engine.watcher import AetherWatcher

        watcher = AetherWatcher(str(tmp_path), debounce_seconds=5.0)
        assert watcher.debounce_seconds == 5.0


# ── Config Tests ──


class TestConfigV2:
    def test_offline_mode_exists(self):
        from aether.config import Config
        assert hasattr(Config, "OFFLINE_MODE")
        assert Config.OFFLINE_MODE is False

    def test_watch_mode_exists(self):
        from aether.config import Config
        assert hasattr(Config, "WATCH_MODE")
        assert Config.WATCH_MODE is False

    def test_verbose_tools_default(self):
        from aether.config import SessionState
        assert hasattr(SessionState, "verbose_tools")
        assert SessionState.verbose_tools is False
