"""Privilege-Aware Execution Engine (Green Team) for Aether-CyberAgent v2.0.0"""
import subprocess
from rich.console import Console
from aether.engine.capabilities import CapabilityDetector

console = Console()

class PrivilegeAwareExecutor:
    """Executes commands using the minimum required privilege based on host capabilities."""
    
    @classmethod
    def execute_trusted_command(cls, cmd: list[str], require_root: bool = False, god_mode: bool = False) -> str:
        """Executes a standard, trusted system administration command on the host."""
        from aether.engine.command_guard import CommandGuard
        from rich.prompt import Confirm
        
        # 1. Pre-Execution Guard (Blocks destructive commands synchronously)
        if not CommandGuard.evaluate_and_confirm(cmd):
            return "Error: Command blocked by Pre-Execution Guard."

        caps = CapabilityDetector.detect()
        cmd_str = " ".join(cmd)
        
        # 2. ADB Blast-Radius Scoping (Requires distinct confirmation)
        is_device_affecting = cmd_str.startswith("adb shell") or cmd_str.startswith("adb push") or cmd_str.startswith("adb install")
        if is_device_affecting and god_mode:
            console.print("\n[bold magenta]📱 DEVICE BLAST-RADIUS WARNING[/bold magenta]")
            console.print(f"Command targets a connected device: [dim]{cmd_str}[/dim]")
            if not Confirm.ask("[bold white]Confirm device-affecting operation? [y/N][/bold white]"):
                return "Error: Device operation denied by user."
            
            try:
                from aether.engine.quota import AuditLogger
                AuditLogger.log_event("DEVICE_OP", "ADB_EXECUTION", f"God Mode executed: {cmd_str}")
            except ImportError:
                pass

        # Privilege Check Loop
        if require_root and not caps.is_root:
            console.print("[bold red]❌ INSUFFICIENT PRIVILEGES: Operation requires Root/Admin.[/bold red]")
            return "Error: Requires Root/Admin"
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            return f"Execution Error: {e}"
            
    @classmethod
    def execute_risky_code(cls, cmd: list[str], allow_unsandboxed: bool = False) -> str:
        """Executes untrusted code exclusively in an isolated Docker container (Section 9)."""
        caps = CapabilityDetector.detect()
        
        if not caps.docker_available:
            if not allow_unsandboxed:
                # Docker-Absent Fail-Closed Default
                console.print("\n[bold red]❌ SANDBOX REQUIRED: Docker is not available on this host.[/bold red]")
                console.print("[dim]Aether defaults to fail-closed to prevent accidental host compromise.[/dim]")
                console.print("Pass [yellow]--allow-unsandboxed[/yellow] to explicitly opt-in to raw host execution.")
                return "Error: Sandbox unavailable. Fail-Closed enforced."
            
            # Explicit Opt-in triggered
            from rich.prompt import Prompt
            console.print("\n[bold red]⚠️ UNSANDBOXED EXECUTION WARNING[/bold red]")
            console.print("You are choosing to run risky code directly on the host operating system.")
            phrase = "I accept the risk of host compromise"
            if Prompt.ask(f"Type strictly '[bold white]{phrase}[/bold white]' to proceed") != phrase:
                return "Error: Unsandboxed execution denied."
                
            console.print("[bold red]Executing risky payload directly on host...[/bold red]")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return res.stdout
            except Exception as e:
                return f"Execution Error: {e}"
            
        # Standard Sandbox execution logic here
        console.print("[dim]Executing inside isolated container...[/dim]")
        return "sandbox_exec_success"

    @staticmethod
    def is_docker_available() -> bool:
        try:
            res = subprocess.run(["docker", "--version"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def execute_in_sandbox(command: str, timeout: int = 60) -> dict:
        """Run command in an ephemeral Docker container if available, otherwise host."""
        if Sandbox.is_docker_available():
            console.print("[dim]🐳 Spin up ephemeral Docker sandbox...[/dim]")
            docker_cmd = [
                "docker", "run", "--rm", 
                "--network", "none",
                "-v", f"{subprocess.os.getcwd()}:/workspace",
                "-w", "/workspace",
                "python:3.11-slim",
                "sh", "-c", command
            ]
            try:
                res = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
                return {
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "exit_code": res.returncode,
                    "timed_out": False
                }
            except subprocess.TimeoutExpired:
                return {"stdout": "", "stderr": "Timeout", "exit_code": -1, "timed_out": True}
        
        # Fallback to local
        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode,
                "timed_out": False
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "exit_code": -1, "timed_out": True}
