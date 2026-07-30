import os
import sys
import json
import hashlib
from pathlib import Path
from rich.console import Console

console = Console()

def verify_self_integrity():
    """Verifies that the compiled binary matches its production manifest hash."""
    if not getattr(sys, 'frozen', False):
        # Running from source (development)
        return True
        
    binary_path = Path(sys.executable)
    manifest_path = binary_path.parent / "aether_manifest.json"
    
    if not manifest_path.exists():
        console.print("[bold red]❌ Integrity verification failed: Missing aether_manifest.json[/bold red]")
        console.print("[yellow]Diagnostic: Ensure you installed via the official installer.[/yellow]")
        sys.exit(1)
        
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        console.print(f"[bold red]❌ Integrity verification failed: Cannot read manifest - {e}[/bold red]")
        sys.exit(1)
        
    expected_hash = manifest.get("sha256")
    if not expected_hash:
        console.print("[bold red]❌ Integrity verification failed: Invalid manifest[/bold red]")
        sys.exit(1)
        
    hasher = hashlib.sha256()
    with open(binary_path, "rb") as afile:
        hasher.update(afile.read())
        
    actual_hash = hasher.hexdigest()
    
    if expected_hash != actual_hash:
        console.print("[bold red]❌ CRITICAL: Integrity verification failed![/bold red]")
        console.print("[red]The Aether executable has been modified, tampered with, or corrupted.[/red]")
        console.print(f"Diagnostic: Expected {expected_hash}, Actual {actual_hash}")
        sys.exit(1)
        
    return True
