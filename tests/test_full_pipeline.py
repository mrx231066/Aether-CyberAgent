"""Integration test suite for Aether-CyberAgent."""

import ast
import tempfile
import os
from pathlib import Path

import pytest

from aether.agents.blue_auditor import BlueTeamAuditor, VulnerabilityFinding, AuditReport
from aether.engine.graph_memory import CodeGraphMemory
from aether.agents.purple_verifier import PurpleTeamVerifier
from aether.reports.sarif import SarifReporter


# ── Test fixtures ──

VULNERABLE_CODE = '''
import os
import subprocess

def process_input(user_data):
    result = eval(user_data)  # CRITICAL: eval on user input
    return result

def run_command(cmd):
    subprocess.Popen(cmd, shell=True)  # HIGH: shell=True

def get_config():
    password = "supersecret123"  # MEDIUM: hardcoded secret
    return password
'''

SAFE_CODE = '''
import ast
import subprocess

def process_input(user_data: str) -> str:
    result = ast.literal_eval(user_data)
    return result

def run_command(cmd: list[str]) -> None:
    subprocess.run(cmd, shell=False, check=True)

def get_config() -> str:
    import os
    password = os.environ.get("APP_PASSWORD", "")
    return password
'''


@pytest.fixture
def vulnerable_file(tmp_path):
    """Create a temporary file with vulnerable code."""
    p = tmp_path / "vulnerable.py"
    p.write_text(VULNERABLE_CODE)
    return str(p)


@pytest.fixture
def vulnerable_dir(tmp_path):
    """Create a temporary directory with vulnerable files."""
    (tmp_path / "main.py").write_text(VULNERABLE_CODE)
    (tmp_path / "utils.py").write_text('import os\nos.system("ls")\n')
    (tmp_path / "safe.py").write_text('def add(a, b):\n    return a + b\n')
    return str(tmp_path)


# ── Blue Team Tests ──

class TestBlueTeamAuditor:
    def test_scan_file_finds_eval(self, vulnerable_file):
        auditor = BlueTeamAuditor()
        findings = auditor.scan_file(vulnerable_file)
        eval_findings = [f for f in findings if 'eval' in f.vulnerability_type.lower() or 'unsafe' in f.vulnerability_type.lower()]
        assert len(eval_findings) > 0
        assert eval_findings[0].severity == 'CRITICAL'
    
    def test_scan_file_finds_shell_true(self, vulnerable_file):
        auditor = BlueTeamAuditor()
        findings = auditor.scan_file(vulnerable_file)
        shell_findings = [f for f in findings if 'shell' in f.vulnerability_type.lower() or 'popen' in f.vulnerability_type.lower() or 'subprocess' in f.vulnerability_type.lower() or 'command' in f.vulnerability_type.lower() or 'injection' in f.vulnerability_type.lower()]
        assert len(shell_findings) > 0
    
    def test_scan_file_finds_hardcoded_secret(self, vulnerable_file):
        auditor = BlueTeamAuditor()
        findings = auditor.scan_file(vulnerable_file)
        secret_findings = [f for f in findings if 'secret' in f.vulnerability_type.lower() or 'hardcoded' in f.vulnerability_type.lower() or 'password' in f.vulnerability_type.lower()]
        assert len(secret_findings) > 0
    
    def test_scan_directory(self, vulnerable_dir):
        auditor = BlueTeamAuditor()
        report = auditor.scan_directory(vulnerable_dir)
        assert isinstance(report, AuditReport)
        assert report.total_files_scanned >= 3
        assert report.total_vulnerabilities > 0
    
    def test_safe_code_no_findings(self, tmp_path):
        safe = tmp_path / "safe.py"
        safe.write_text('def add(a: int, b: int) -> int:\n    return a + b\n')
        auditor = BlueTeamAuditor()
        findings = auditor.scan_file(str(safe))
        assert len(findings) == 0


# ── Graph Memory Tests ──

class TestCodeGraphMemory:
    def test_build_from_directory(self, vulnerable_dir):
        graph = CodeGraphMemory()
        graph.build_from_directory(vulnerable_dir)
        nodes = graph.get_file_nodes()
        assert len(nodes) >= 3
    
    def test_blast_radius(self, tmp_path):
        # Create files with import dependencies
        (tmp_path / "core.py").write_text('def core_func():\n    pass\n')
        (tmp_path / "utils.py").write_text('import core\ndef util_func():\n    core.core_func()\n')
        (tmp_path / "main.py").write_text('import utils\nimport core\n')
        
        graph = CodeGraphMemory()
        graph.build_from_directory(str(tmp_path))
        # core.py being vulnerable should show blast radius
        blast = graph.get_blast_radius(str(tmp_path / "core.py"))
        assert isinstance(blast, dict)
        assert 'affected_files' in blast


# ── Purple Team Tests ──

class TestPurpleTeamVerifier:
    def test_safe_code_passes(self):
        verifier = PurpleTeamVerifier()
        result = verifier.verify_patch(
            original_code=VULNERABLE_CODE,
            patched_code=SAFE_CODE,
            vulnerability_type='eval_call',
        )
        assert result.z3_result in ('verified', 'skipped')
    
    def test_vulnerable_code_fails_z3(self):
        verifier = PurpleTeamVerifier()
        result = verifier.verify_patch(
            original_code=VULNERABLE_CODE,
            patched_code=VULNERABLE_CODE,  # Patched with same vulnerable code
            vulnerability_type='eval_call',
        )
        assert result.z3_result == 'failed'


# ── SARIF Reporter Tests ──

class TestSarifReporter:
    def test_generate_empty_report(self):
        from aether.agents.gold_autonomic import PipelineResult
        reporter = SarifReporter()
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
        report = reporter.generate_report(result)
        assert report['version'] == '2.1.0'
        assert len(report['runs']) == 1
    
    def test_sarif_with_findings(self):
        from aether.agents.gold_autonomic import PipelineResult
        reporter = SarifReporter()
        result = PipelineResult(
            success=True,
            files_scanned=1,
            vulnerabilities_found=1,
            vulnerabilities_fixed=1,
            verified_patches=[{
                'file': '/tmp/test.py',
                'original_code': VULNERABLE_CODE,
                'patched_code': SAFE_CODE,
                'vulnerability_title': 'eval() on user input',
                'severity': 'CRITICAL',
                'fix_rationale': 'Replaced eval with ast.literal_eval',
                'attempts': 1,
                'findings': [{'type': 'eval_call', 'severity': 'CRITICAL', 'line': 5, 'description': 'eval() call'}],
                'verification': {'z3': 'verified', 'hypothesis': 'passed'},
            }],
            failed_patches=[],
            scan_duration=1.5,
            state_log=[],
        )
        report = reporter.generate_report(result)
        assert len(report['runs'][0]['results']) > 0


# ── Gemini Client Model Discovery Tests ──

class TestGeminiClientModelDiscovery:
    def test_get_available_models_fallback_without_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        from aether.ai.gemini_client import GeminiClient
        models = GeminiClient.get_available_models(api_key=None)
        assert isinstance(models, list)
        assert len(models) > 0
        model_names = [m["name"] for m in models]
        assert any("gemini-" in name for name in model_names)

    def test_get_available_models_mock_discovery(self):
        from unittest.mock import MagicMock, patch
        from aether.ai.gemini_client import GeminiClient

        mock_m1 = MagicMock()
        mock_m1.name = "models/gemini-2.5-pro"
        mock_m1.supported_actions = ["generateContent"]

        mock_m2 = MagicMock()
        mock_m2.name = "models/gemini-2.5-flash"
        mock_m2.supported_actions = ["generateContent"]

        mock_m3 = MagicMock()
        mock_m3.name = "models/text-embedding-004"
        mock_m3.supported_actions = ["embedContent"]

        with patch("google.genai.Client") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.models.list.return_value = [mock_m1, mock_m2, mock_m3]

            models = GeminiClient.get_available_models(api_key="fake_key")
            model_names = [m["name"] for m in models]
            assert "gemini-2.5-flash" in model_names
            assert "gemini-2.5-pro" in model_names
            assert "text-embedding-004" not in model_names

    def test_gemini_client_custom_model(self):
        from unittest.mock import patch
        from aether.ai.gemini_client import GeminiClient
        with patch("google.genai.Client"):
            client = GeminiClient(api_key="fake_key", model="gemini-2.5-pro")
            assert client.model == "gemini-2.5-pro"

