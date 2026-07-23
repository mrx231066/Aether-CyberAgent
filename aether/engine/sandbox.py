"""Green Team: Docker Sandbox Environment for Test Execution."""

import os
import tempfile
import subprocess
import shutil
from dataclasses import dataclass
from rich.console import Console

console = Console()

try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


@dataclass
class SandboxResult:
    """Result of test execution inside the sandbox."""
    passed: bool
    exit_code: int
    stdout: str
    stderr: str


class DockerSandbox:
    """Green Team: Secure isolated execution of patches and tests."""
    
    def __init__(self, image: str = 'python:3.11-slim'):
        """Initialize the Docker sandbox."""
        self.image = image
        self.client = None
        self.use_docker = False
        
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                self.client.ping()
                self.use_docker = True
                self._ensure_image()
            except Exception:
                console.print("[yellow]Warning: Docker daemon is not available. Falling back to local execution.[/yellow]")
        else:
            console.print("[yellow]Warning: 'docker' python package is not installed. Falling back to local execution.[/yellow]")

    def _ensure_image(self):
        """Ensure the required Docker image is available."""
        if not self.use_docker or not self.client:
            return
            
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            with console.status(f"[bold blue]Pulling Docker image {self.image}..."):
                self.client.images.pull(self.image)
                
    def execute_test(self, patched_code: str, test_script: str) -> SandboxResult:
        """Run the test script against the patched code in an isolated environment."""
        temp_dir = tempfile.mkdtemp(prefix='aether_sandbox_')
        
        try:
            # Write patched code
            code_path = os.path.join(temp_dir, 'module.py')
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(patched_code)
                
            # Write test script
            test_path = os.path.join(temp_dir, 'test_module.py')
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_script)
                
            # Create runner script
            runner_script = (
                "#!/bin/bash\n"
                "pip install --quiet pytest hypothesis\n"
                "pytest test_module.py -v\n"
            )
            runner_path = os.path.join(temp_dir, 'run.sh')
            with open(runner_path, 'w', encoding='utf-8') as f:
                f.write(runner_script)
            os.chmod(runner_path, 0o755)

            if self.use_docker and self.client:
                return self._run_in_docker(temp_dir)
            else:
                return self._run_locally(temp_dir)
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def _run_in_docker(self, temp_dir: str) -> SandboxResult:
        """Execute the tests inside a Docker container."""
        if not self.client:
            return self._run_locally(temp_dir)
            
        container = None
        try:
            container = self.client.containers.run(
                self.image,
                command=["/bin/bash", "run.sh"],
                volumes={temp_dir: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                detach=True,
                remove=False,
                stdout=True,
                stderr=True
            )
            
            result = container.wait(timeout=120)
            exit_code = result['StatusCode']
            
            stdout_logs = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr_logs = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
            
            return SandboxResult(
                passed=(exit_code == 0),
                exit_code=exit_code,
                stdout=stdout_logs,
                stderr=stderr_logs
            )
            
        except Exception as e:
            return SandboxResult(
                passed=False,
                exit_code=-1,
                stdout="",
                stderr=f"Docker execution failed: {str(e)}"
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _run_locally(self, temp_dir: str) -> SandboxResult:
        """Fallback: Execute the tests locally."""
        try:
            process = subprocess.run(
                ["/bin/bash", "run.sh"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return SandboxResult(
                passed=(process.returncode == 0),
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr
            )
        except subprocess.TimeoutExpired as e:
            return SandboxResult(
                passed=False,
                exit_code=-1,
                stdout=e.stdout.decode('utf-8') if isinstance(e.stdout, bytes) else (e.stdout or ""),
                stderr="Execution timed out."
            )
        except Exception as e:
            return SandboxResult(
                passed=False,
                exit_code=-1,
                stdout="",
                stderr=f"Local execution failed: {str(e)}"
            )
