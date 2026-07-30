"""Capability Detection Engine for Aether-CyberAgent v2.0.0"""

import os
import platform
import subprocess
from dataclasses import dataclass
from rich.console import Console

console = Console()

@dataclass
class DeviceCapabilities:
    os_name: str
    architecture: str
    is_root: bool
    adb_available: bool
    adb_authorized: bool
    docker_available: bool

class CapabilityDetector:
    """Detects available system privileges and execution environments."""

    @classmethod
    def detect(cls) -> DeviceCapabilities:
        console.print("[dim]🔍 Detecting device capabilities...[/dim]")
        
        os_name = platform.system()
        arch = platform.machine()
        
        # Check Root / Admin
        is_root = False
        try:
            if os_name == "Windows":
                import ctypes
                is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_root = os.geteuid() == 0
        except AttributeError:
            pass

        # Check ADB availability and authorization
        adb_avail = False
        adb_auth = False
        try:
            adb_res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
            if adb_res.returncode == 0:
                adb_avail = True
                if "device" in adb_res.stdout and "unauthorized" not in adb_res.stdout:
                    adb_auth = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check Docker (for sandbox capabilities)
        docker_avail = False
        try:
            doc_res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            docker_avail = doc_res.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        caps = DeviceCapabilities(
            os_name=os_name,
            architecture=arch,
            is_root=is_root,
            adb_available=adb_avail,
            adb_authorized=adb_auth,
            docker_available=docker_avail
        )
        
        cls._print_summary(caps)
        return caps

    @staticmethod
    def _print_summary(caps: DeviceCapabilities):
        console.print("[bold cyan]⚙️ Device Capability Profile:[/bold cyan]")
        
        if caps.is_root:
            console.print("  [bold red]▶ ROOT/ADMIN:[/bold red] Direct host-level operations available.")
        elif caps.adb_authorized:
            console.print("  [bold yellow]▶ ADB AUTHORIZED:[/bold yellow] Device administration through ADB capabilities.")
        else:
            console.print("  [bold green]▶ STANDARD USER:[/bold green] Operating strictly within user-level APIs.")
            
        if not caps.docker_available:
            console.print("  [dim]▶ SANDBOX:[/dim] [yellow]Docker unavailable. High-risk execution disabled.[/yellow]")
