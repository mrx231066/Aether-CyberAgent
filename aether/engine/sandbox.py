"""Docker Execution Sandbox for Aether-CyberAgent v1.0.0"""
import subprocess
from rich.console import Console

console = Console()

class Sandbox:
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
