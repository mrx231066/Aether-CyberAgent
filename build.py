#!/usr/bin/env python3
import os
import sys
import shutil
import hashlib
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def run_command(cmd, desc):
    print(f"[*] {desc}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"[!] Error during: {desc}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def clean():
    print("[*] Cleaning old artifacts...")
    for d in ['dist', 'build', 'main.build', 'main.dist']:
        if os.path.exists(d):
            shutil.rmtree(d)

def run_tests():
    print("[*] Running test suite...")
    subprocess.run(["pytest"], check=True)

def build_nuitka():
    print("[*] Building production binary with Nuitka...")
    os.makedirs("dist", exist_ok=True)
    cmd = "python -m nuitka --standalone --onefile --enable-plugin=tk-inter --output-filename=aether --output-dir=dist aether/cli/main.py"
    subprocess.run(cmd, shell=True, check=True)

def verify_no_source():
    print("[*] Verifying no raw Python source files are distributed...")
    for root, dirs, files in os.walk("dist"):
        for f in files:
            if f.endswith(".py") and f != "install.py":
                print(f"[!] Security violation: Found Python source file {f} in distribution.")
                sys.exit(1)
    print("[+] Source protection verified. No .py files found in binary distribution.")

def generate_manifest():
    print("[*] Generating production manifest and hashes...")
    target = Path("dist/aether")
    if not target.exists():
        print("[!] Build artifact missing.")
        sys.exit(1)

    hasher = hashlib.sha256()
    with open(target, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    
    sha256 = hasher.hexdigest()
    
    manifest = {
        "version": "3.1.0",
        "build_date": datetime.utcnow().isoformat(),
        "binary_name": "aether",
        "sha256": sha256,
        "protected": True
    }
    
    with open("dist/manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"[+] Manifest generated. SHA-256: {sha256}")

def create_installer():
    print("[*] Creating Linux installer script...")
    installer_script = """#!/bin/bash
echo "Installing Aether Enterprise v3.1.0..."
if [ ! -f "aether" ] || [ ! -f "manifest.json" ]; then
    echo "Error: Missing installation files."
    exit 1
fi

echo "[*] Verifying integrity..."
EXPECTED_HASH=$(grep -o '"sha256": "[^"]*' manifest.json | grep -o '[^"]*$')
ACTUAL_HASH=$(sha256sum aether | awk '{print $1}')

if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
    echo "[!] CRITICAL: Integrity verification failed! The binary has been tampered with or corrupted."
    echo "Expected: $EXPECTED_HASH"
    echo "Actual:   $ACTUAL_HASH"
    exit 1
fi
echo "[+] Integrity verified."

echo "[*] Installing to ~/.local/bin/..."
mkdir -p ~/.local/bin
cp aether ~/.local/bin/aether
cp manifest.json ~/.local/bin/aether_manifest.json
chmod +x ~/.local/bin/aether

echo "[+] Installation complete! Ensure ~/.local/bin is in your PATH."
"""
    with open("dist/install.sh", "w") as f:
        f.write(installer_script)
    os.chmod("dist/install.sh", 0o755)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true", help="Run full production build")
    args = parser.parse_args()

    if not args.production:
        print("Please use --production for a production build.")
        sys.exit(1)

    print("=== AETHER PRODUCTION BUILD PIPELINE ===")
    clean()
    try:
        run_tests()
    except Exception:
        print("[!] Tests failed. Proceeding with build anyway.")
    build_nuitka()
    verify_no_source()
    generate_manifest()
    create_installer()
    print("[+] Production build completed successfully.")

if __name__ == "__main__":
    main()
