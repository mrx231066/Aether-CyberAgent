"""Gold Team: Autonomic Self-Correction Engine.

The orchestrator that manages the self-healing security pipeline.
If verification fails, it intercepts the failure trace, rolls back
the system state, updates the prompt context, and retries.
"""

import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from aether.agents.blue_auditor import BlueTeamAuditor, AuditReport, VulnerabilityFinding
from aether.ai.gemini_client import GeminiClient, RemediationResult
from aether.agents.purple_verifier import PurpleTeamVerifier, VerificationResult
from aether.engine.graph_memory import CodeGraphMemory

console = Console()


@dataclass
class PipelineState:
    """Tracks the current state of the autonomic pipeline."""
    phase: str = 'idle'
    current_file: Optional[str] = None
    attempt: int = 0
    max_retries: int = 3
    audit_report: Optional[AuditReport] = None
    remediation: Optional[RemediationResult] = None
    verification: Optional[VerificationResult] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass 
class PipelineResult:
    """Final result of the autonomic pipeline."""
    success: bool
    files_scanned: int
    vulnerabilities_found: int
    vulnerabilities_fixed: int
    verified_patches: List[Dict[str, Any]]  # List of {file, original, patched, finding, verification}
    failed_patches: List[Dict[str, Any]]   # Patches that failed verification after max retries
    scan_duration: float
    state_log: List[Dict[str, Any]]        # Full state history for dashboard


class AutonomicEngine:
    """Gold Team: The self-healing orchestrator.
    
    Manages the full pipeline:
    1. Blue Team scans for vulnerabilities
    2. Yellow Team generates patches via Gemini
    3. Purple Team verifies patches with Z3 + Hypothesis  
    4. If verification fails, retry with error context (up to max_retries)
    5. Output verified patches and state log
    """
    
    def __init__(self, max_retries: int = 3, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        """Initialize the Autonomic Engine."""
        self.max_retries = max_retries
        self.blue_team = BlueTeamAuditor()
        self.yellow_team = GeminiClient(api_key=api_key, model=model)
        self.purple_team = PurpleTeamVerifier()
        self.graph_memory = CodeGraphMemory()
        self.state = PipelineState(max_retries=max_retries)
        self.state_log_path = Path('.aether/state_log.json')
    
    def execute_scan(self, target_path: str) -> PipelineResult:
        """Execute the full autonomic security scan pipeline.
        
        Args:
            target_path: Path to the directory to scan.
            
        Returns:
            PipelineResult containing the scan results.
        """
        from aether.engine.quota import AuditLogger, QuotaEngine
        from aether.agents.orange_intel import OrangeTeamIntel

        self.state_log = []
        start_time = time.time()
        
        AuditLogger.log_event("GOLD_TEAM", "SCAN_START", f"Target: {target_path}")

        # Step 0: Orange Team OSINT
        orange_team = OrangeTeamIntel()
        orange_team.monitor_public_feeds()
        orange_team.report_intel()

        # Step 1: Blue Team Static Analysis
        self._log_state("blue_team_start", phase="audit")
        self.state.start_time = time.time()
        self.state.phase = 'initializing'
        
        # Ensure .aether directory exists
        Path('.aether/reports').mkdir(parents=True, exist_ok=True)
        
        # Display banner
        self._display_banner()
        
        # STEP 1: Build dependency graph
        console.print("\n[bold cyan]🗺️  Building dependency graph...[/]")
        self.graph_memory.build_from_directory(target_path)
        
        # STEP 2: Blue Team Audit
        self.state.phase = 'blue_team_audit'
        console.print("\n[bold blue]🔵 Blue Team: Starting static analysis...[/]")
        audit_report = self.blue_team.scan_directory(target_path)
        self.state.audit_report = audit_report
        
        self._display_audit_summary(audit_report)
        
        if not audit_report.findings:
            console.print("\n[bold green]✅ No vulnerabilities found. Codebase is clean![/]")
            self.state.end_time = time.time()
            return PipelineResult(
                success=True,
                files_scanned=audit_report.total_files_scanned,
                vulnerabilities_found=0,
                vulnerabilities_fixed=0,
                verified_patches=[],
                failed_patches=[],
                scan_duration=self.state.end_time - self.state.start_time,
                state_log=self.state.history,
            )
        
        # STEP 3: Process each vulnerability through the self-healing loop
        verified_patches = []
        failed_patches = []
        
        # Group findings by file
        findings_by_file: Dict[str, List[VulnerabilityFinding]] = {}
        for finding in audit_report.findings:
            findings_by_file.setdefault(finding.file_path, []).append(finding)
        
        for file_path, findings in findings_by_file.items():
            console.print(f"\n[bold yellow]📄 Processing: {file_path}[/]")
            
            # Read the source code
            try:
                source_code = Path(file_path).read_text()
            except Exception as e:
                console.print(f"[red]  ❌ Could not read file: {e}[/]")
                continue
            
            # Build the blue team report for this file
            blue_report = {
                'file': file_path,
                'findings': [
                    {
                        'type': f.vulnerability_type,
                        'severity': f.severity,
                        'line': f.line_number,
                        'description': f.description,
                        'snippet': f.code_snippet,
                    }
                    for f in findings
                ],
            }
            
            # Get blast radius
            blast = self.graph_memory.get_blast_radius(file_path)
            if blast['affected_files']:
                console.print(f"  [dim]💥 Blast radius: {len(blast['affected_files'])} dependent files[/]")
            
            # Self-healing loop
            result = self._execute_self_healing_loop(
                source_code=source_code,
                blue_report=blue_report,
                file_path=file_path,
            )
            
            if result:
                verified_patches.append(result)
            else:
                failed_patches.append({
                    'file': file_path,
                    'findings': [f.model_dump() if hasattr(f, 'model_dump') else vars(f) for f in findings],
                    'reason': 'Exhausted all retries',
                })
        
        # Save state log
        self._save_state_log()
        
        self.state.end_time = time.time()
        self.state.phase = 'complete'
        
        pipeline_result = PipelineResult(
            success=len(failed_patches) == 0,
            files_scanned=audit_report.total_files_scanned,
            vulnerabilities_found=audit_report.total_vulnerabilities,
            vulnerabilities_fixed=sum(len(p.get('findings', [])) for p in verified_patches),
            verified_patches=verified_patches,
            failed_patches=failed_patches,
            scan_duration=self.state.end_time - self.state.start_time,
            state_log=self.state.history,
        )
        
        self._display_final_summary(pipeline_result)
        return pipeline_result
    
    def _execute_self_healing_loop(
        self,
        source_code: str,
        blue_report: Dict[str, Any],
        file_path: str,
    ) -> Optional[Dict[str, Any]]:
        """The core self-healing loop.
        
        Args:
            source_code: The original source code of the file.
            blue_report: The findings report for this file.
            file_path: The path to the file.
            
        Returns:
            A dictionary containing the verified patch details, or None if failed.
        """
        previous_failure_trace = None
        
        for attempt in range(1, self.max_retries + 1):
            self.state.attempt = attempt
            self.state.current_file = file_path
            
            # Yellow Team: Generate patch
            self.state.phase = 'yellow_team_patch'
            console.print(f"\n  [bold yellow]🟡 Yellow Team (Attempt {attempt}/{self.max_retries}): Generating patch via Gemini...[/]")
            
            try:
                remediation = self.yellow_team.request_patch(
                    source_code=source_code,
                    blue_team_report=blue_report,
                    previous_failure_trace=previous_failure_trace,
                )
                self.state.remediation = remediation
                console.print(f"    ✅ Patch generated: {remediation.vulnerability_title}")
                console.print(f"    📋 Severity: {remediation.severity_level}")
            except Exception as e:
                console.print(f"    [red]❌ Gemini API error: {e}[/]")
                self._log_state('yellow_team_error', {'error': str(e), 'attempt': attempt})
                continue
            
            # Purple Team: Verify patch
            self.state.phase = 'purple_team_verify'
            console.print(f"\n  [bold magenta]🟣 Purple Team: Formal verification...[/]")
            
            try:
                verification = self.purple_team.verify_patch(
                    original_code=source_code,
                    patched_code=remediation.patched_code,
                    vulnerability_type=blue_report['findings'][0]['type'],
                )
                self.state.verification = verification
            except Exception as e:
                console.print(f"    [red]❌ Verification error: {e}[/]")
                self._log_state('purple_team_error', {'error': str(e), 'attempt': attempt})
                continue
            
            if verification.passed:
                console.print("    [bold green]✅ Z3: VERIFIED[/]")
                console.print("    [bold green]✅ Hypothesis: PASSED[/]")
                
                self._log_state('verification_passed', {
                    'attempt': attempt,
                    'file': file_path,
                })
                
                return {
                    'file': file_path,
                    'original_code': source_code,
                    'patched_code': remediation.patched_code,
                    'vulnerability_title': remediation.vulnerability_title,
                    'severity': remediation.severity_level,
                    'fix_rationale': remediation.fix_rationale,
                    'attempts': attempt,
                    'findings': blue_report['findings'],
                    'verification': {
                        'z3': verification.z3_result,
                        'hypothesis': verification.hypothesis_result,
                    },
                }
            else:
                console.print(f"    [bold red]❌ Verification FAILED[/]")
                for detail in verification.details:
                    console.print(f"      {detail}")
                
                # Gold Team intervention: capture failure, update context
                previous_failure_trace = verification.error_trace
                console.print(f"\n  [bold gold1]🧀 Gold Team: Intercepted failure. Updating context for retry...[/]")
                
                self._log_state('verification_failed', {
                    'attempt': attempt,
                    'file': file_path,
                    'error': verification.error_trace,
                })
        
        console.print(f"\n  [bold red]❌ Exhausted {self.max_retries} retries for {file_path}[/]")
        return None
    
    def _display_banner(self) -> None:
        """Display the Aether banner."""
        banner = Panel(
            "[bold cyan]🛡️  AETHER-CYBERAGENT[/]\n"
            "[dim]Autonomous Multi-Agent AI Security Platform[/]\n"
            f"[dim]v2.0.0 | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}[/]",
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 4),
        )
        console.print(banner)
    
    def _display_audit_summary(self, report: AuditReport) -> None:
        """Display the Blue Team audit summary.
        
        Args:
            report: The audit report to display.
        """
        table = Table(title="🔵 Blue Team Audit Results", box=box.ROUNDED, border_style="blue")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow", justify="right")
        table.add_column("Type", style="red")
        table.add_column("Severity", style="magenta")
        table.add_column("Description", style="white")
        
        for f in report.findings:
            severity_style = {
                'CRITICAL': '[bold red]',
                'HIGH': '[red]',
                'MEDIUM': '[yellow]',
                'LOW': '[green]',
            }.get(f.severity, '')
            table.add_row(
                f.file_path, str(f.line_number), f.vulnerability_type,
                f"{severity_style}{f.severity}", f.description,
            )
        
        console.print(table)
        console.print(f"\n  Files scanned: {report.total_files_scanned}")
        console.print(f"  Vulnerabilities found: {report.total_vulnerabilities}")
    
    def _display_final_summary(self, result: PipelineResult) -> None:
        """Display the final pipeline summary.
        
        Args:
            result: The pipeline result to display.
        """
        status = "[bold green]✅ ALL CLEAR" if result.success else "[bold yellow]⚠️ PARTIAL"
        
        panel = Panel(
            f"{status}[/]\n\n"
            f"  Files scanned:          {result.files_scanned}\n"
            f"  Vulnerabilities found:  {result.vulnerabilities_found}\n"
            f"  Vulnerabilities fixed:  {result.vulnerabilities_fixed}\n"
            f"  Failed patches:         {len(result.failed_patches)}\n"
            f"  Duration:               {result.scan_duration:.2f}s",
            title="🛡️ Aether-CyberAgent Scan Complete",
            box=box.DOUBLE,
            border_style="green" if result.success else "yellow",
            padding=(1, 2),
        )
        console.print("\n")
        console.print(panel)
    
    def _log_state(self, event: str, data: Dict[str, Any]) -> None:
        """Log a state transition.
        
        Args:
            event: The event name.
            data: The event data.
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event': event,
            'phase': self.state.phase,
            **data,
        }
        self.state.history.append(entry)
    
    def _save_state_log(self) -> None:
        """Save the state log to disk for dashboard consumption."""
        self.state_log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_log_path, 'w') as f:
                json.dump(self.state.history, f, indent=2, default=str)
        except Exception as e:
            console.print(f"[red]Failed to save state log: {e}[/]")

    def execute_and_correct_loop(
        self,
        user_prompt: str,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute an autonomous script generation and self-correction loop.

        1. Yellow Team generates a script from the user prompt.
        2. Green Team executes the script via ToolEngine.
        3. If execution fails (exit code != 0 or traceback detected):
           - Gold Team captures stderr and traceback.
           - Feeds failure context back to Yellow Team for auto-fix.
           - Retries up to max_retries times.

        Args:
            user_prompt: Task description from the user.
            max_retries: Max correction attempts (defaults to self.max_retries).

        Returns:
            Dict with keys: success, script, stdout, stderr, attempts, history.
        """
        from aether.agents.yellow_patcher import YellowPatcher
        from aether.engine.tools import ToolEngine

        retries = max_retries if max_retries is not None else self.max_retries
        tools = ToolEngine()
        history = []

        # Initialize Yellow Patcher for script generation
        try:
            patcher = YellowPatcher(
                api_key=self.yellow_team.api_key,
                model=self.yellow_team.model,
            )
        except Exception as e:
            return {
                "success": False,
                "script": None,
                "stdout": "",
                "stderr": f"Failed to initialize Yellow Patcher: {e}",
                "attempts": 0,
                "history": [],
            }

        console.print(
            Panel(
                f"[bold white]Task:[/bold white] {user_prompt}",
                title="🥇 Gold Team: Autonomous Execution Loop",
                border_style="yellow",
            )
        )

        current_prompt = user_prompt
        last_script = None
        last_stdout = ""
        last_stderr = ""

        for attempt in range(1, retries + 1):
            console.print(
                f"\n[bold yellow]🔄 Attempt {attempt}/{retries}[/bold yellow]"
            )

            # Step 1: Yellow Team generates script
            console.print("[bold cyan]🟡 Yellow Team: Generating script...[/bold cyan]")
            script = patcher.generate_script(current_prompt)

            if not script:
                console.print("[red]❌ Yellow Team failed to generate a script.[/red]")
                history.append({
                    "attempt": attempt,
                    "phase": "generation",
                    "success": False,
                    "error": "No script generated",
                })
                continue

            last_script = script

            # Show the generated script
            from rich.syntax import Syntax
            console.print(
                Panel(
                    Syntax(script, "python", theme="monokai", line_numbers=True),
                    title=f"Generated Script (Attempt {attempt})",
                    border_style="cyan",
                )
            )

            # Step 2: Green Team executes the script
            console.print("[bold green]🟢 Green Team: Executing script...[/bold green]")
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir="."
            ) as f:
                f.write(script)
                script_path = f.name

            result = tools.execute_shell(f"python {script_path}", timeout=60)
            last_stdout = result["stdout"]
            last_stderr = result["stderr"]
            exit_code = result["exit_code"]

            # Clean up temp file
            try:
                Path(script_path).unlink()
            except OSError:
                pass

            if result["stdout"]:
                console.print(
                    Panel(result["stdout"].strip()[:2000], title="stdout", border_style="green")
                )
            if result["stderr"]:
                console.print(
                    Panel(result["stderr"].strip()[:2000], title="stderr", border_style="red")
                )

            history.append({
                "attempt": attempt,
                "phase": "execution",
                "exit_code": exit_code,
                "stdout": last_stdout[:500],
                "stderr": last_stderr[:500],
                "timed_out": result["timed_out"],
            })

            # Step 3: Check result
            if exit_code == 0 and not self._has_traceback(last_stderr):
                console.print(
                    f"[bold green]✅ Script executed successfully on attempt {attempt}.[/bold green]"
                )
                return {
                    "success": True,
                    "script": last_script,
                    "stdout": last_stdout,
                    "stderr": last_stderr,
                    "attempts": attempt,
                    "history": history,
                }

            # Step 4: Gold Team intercepts failure and feeds back to Yellow
            console.print(
                "[bold yellow]🥇 Gold Team: Intercepting failure, preparing corrective prompt...[/bold yellow]"
            )
            error_context = last_stderr if last_stderr else f"Exit code: {exit_code}"
            current_prompt = (
                f"The previous script failed with the following error:\n\n"
                f"```\n{error_context}\n```\n\n"
                f"Original task: {user_prompt}\n\n"
                f"Please fix the script to resolve this error. "
                f"Return the complete corrected script."
            )

        # All retries exhausted
        console.print(
            f"[bold red]❌ All {retries} attempts exhausted. Script could not be auto-fixed.[/bold red]"
        )
        return {
            "success": False,
            "script": last_script,
            "stdout": last_stdout,
            "stderr": last_stderr,
            "attempts": retries,
            "history": history,
        }

    @staticmethod
    def _has_traceback(stderr: str) -> bool:
        """Check if stderr contains a Python traceback."""
        traceback_indicators = ["Traceback (most recent call last)", "Error:", "Exception:"]
        return any(indicator in stderr for indicator in traceback_indicators)

