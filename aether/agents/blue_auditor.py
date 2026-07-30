import ast
import os
import datetime
from datetime import timezone
from pathlib import Path
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()

class VulnerabilityFinding(BaseModel):
    """Pydantic model representing a single vulnerability finding."""
    file_path: str
    line_number: int
    vulnerability_type: str
    severity: str
    description: str
    code_snippet: str

class AuditReport(BaseModel):
    """Pydantic model representing the overall audit report."""
    findings: List[VulnerabilityFinding]
    total_files_scanned: int
    total_vulnerabilities: int
    scan_timestamp: str

class VulnerabilityVisitor(ast.NodeVisitor):
    """AST Node visitor for detecting security vulnerabilities."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[VulnerabilityFinding] = []
        self.source_lines: List[str] = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.source_lines = f.readlines()
        except OSError:
            pass

    def _get_snippet(self, line_number: int, context: int = 2) -> str:
        """Extract a code snippet with surrounding context lines."""
        if not self.source_lines or line_number <= 0:
            return ""
            
        start_idx = max(0, line_number - 1 - context)
        end_idx = min(len(self.source_lines), line_number + context)
        return "".join(self.source_lines[start_idx:end_idx]).strip()

    def _add_finding(self, node: ast.AST, vul_type: str, severity: str, desc: str):
        line_num = getattr(node, "lineno", 0)
        self.findings.append(
            VulnerabilityFinding(
                file_path=self.file_path,
                line_number=line_num,
                vulnerability_type=vul_type,
                severity=severity,
                description=desc,
                code_snippet=self._get_snippet(line_num)
            )
        )

    def visit_Call(self, node: ast.Call) -> Any:
        """Check for dangerous function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name == "eval":
                self._add_finding(node, "Unsafe Eval", "CRITICAL", "Usage of eval() can lead to arbitrary code execution.")
            elif func_name == "exec":
                self._add_finding(node, "Unsafe Exec", "CRITICAL", "Usage of exec() can lead to arbitrary code execution.")
            elif func_name == "__import__":
                self._add_finding(node, "Dynamic Import", "MEDIUM", "Usage of __import__() might lead to loading malicious modules.")
                
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                
                # Subprocess checks
                if module_name == "subprocess" and attr_name in ("Popen", "call", "run"):
                    has_shell_true = any(
                        isinstance(kw.value, ast.Constant) and kw.value.value is True 
                        for kw in node.keywords if kw.arg == "shell"
                    )
                    if has_shell_true:
                        self._add_finding(
                            node, 
                            "Command Injection", 
                            "HIGH", 
                            f"subprocess.{attr_name} called with shell=True is prone to command injection."
                        )
                        
                # OS system checks
                elif module_name == "os" and attr_name == "system":
                    self._add_finding(node, "Command Injection", "HIGH", "os.system() is prone to command injection.")
                    
                # Pickle checks
                elif module_name == "pickle" and attr_name in ("load", "loads"):
                    self._add_finding(node, "Insecure Deserialization", "HIGH", f"pickle.{attr_name}() is unsafe against maliciously constructed data.")
                    
                # YAML checks
                elif module_name == "yaml" and attr_name == "load":
                    has_safe_loader = any(
                        kw.arg == "Loader" and isinstance(kw.value, ast.Attribute) and kw.value.attr == "SafeLoader"
                        for kw in node.keywords
                    )
                    if not has_safe_loader:
                        # Check positional args as well if needed, but kwargs is standard pattern
                        self._add_finding(node, "Unsafe YAML Load", "MEDIUM", "yaml.load() without SafeLoader can execute arbitrary code.")

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        """Check for hardcoded secrets."""
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(secret_term in var_name for secret_term in ["password", "secret", "api_key", "token"]):
                        self._add_finding(
                            node,
                            "Hardcoded Secret",
                            "MEDIUM",
                            f"Potential hardcoded secret found in variable '{target.id}'."
                        )
        self.generic_visit(node)


class BlueTeamAuditor:
    """Auditor engine for static analysis and vulnerability detection."""
    
    def scan_file(self, file_path: str) -> List[VulnerabilityFinding]:
        """Parse a single file's AST and run the vulnerability visitor."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
            
            visitor = VulnerabilityVisitor(file_path=file_path)
            visitor.visit(tree)
            return visitor.findings
        except (SyntaxError, UnicodeDecodeError, OSError) as e:
            console.print(f"[yellow]Warning: Could not parse {file_path} - {str(e)}[/yellow]")
            return []

    def scan_directory(self, directory: str) -> AuditReport:
        """Scan all .py files in a directory recursively for vulnerabilities."""
        root_path = Path(directory).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        all_findings: List[VulnerabilityFinding] = []
        files_scanned = 0

        console.print(f"[bold blue]Starting Static Analysis Audit on {root_path}...[/bold blue]")
        
        import os
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = str((Path(root) / file).resolve())
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)
                    files_scanned += 1
                    
        total_vulnerabilities = len(all_findings)
        
        console.print(f"[bold green]Audit complete. Scanned {files_scanned} files, found {total_vulnerabilities} vulnerabilities.[/bold green]")
        
        return AuditReport(
            findings=all_findings,
            total_files_scanned=files_scanned,
            total_vulnerabilities=total_vulnerabilities,
            scan_timestamp=datetime.datetime.now(timezone.utc).isoformat()
        )

class IncidentResponse:
    """Blue Team Incident Response & Containment (CISA Lifecycle)."""
    
    @staticmethod
    def isolate_host(ip_address: str):
        """Simulate host network isolation (EDR-style containment)."""
        console.print(f"\n[bold blue]🔵 Blue Team: Triggering Containment for {ip_address}[/bold blue]")
        console.print("  [dim]- Rotating localized credentials...[/dim]")
        console.print("  [dim]- Dropping active network sessions...[/dim]")
        
        # We check if AuditLogger exists and log
        try:
            from aether.engine.quota import AuditLogger
            AuditLogger.log_event("BLUE_TEAM", "CONTAINMENT", f"Isolated host {ip_address}", severity="CRITICAL")
        except ImportError:
            pass

    def get_source_snippet(self, file_path: str, line_number: int, context: int = 2) -> str:
        """Extract a code snippet around a specific line in a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            start_idx = max(0, line_number - 1 - context)
            end_idx = min(len(lines), line_number + context)
            return "".join(lines[start_idx:end_idx]).strip()
        except OSError:
            return ""
