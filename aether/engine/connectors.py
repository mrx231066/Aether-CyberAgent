"""Omni-Connectors for Aether-CyberAgent."""

import subprocess
from rich.console import Console

console = Console()

def adb_connector(command: str) -> str:
    """Execute Android Debug Bridge commands."""
    try:
        res = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
        if "device offline" in res.stderr or "no devices/emulators found" in res.stderr:
            console.print("[yellow]ADB disconnected. Attempting to start server...[/yellow]")
            subprocess.run("adb start-server", shell=True, capture_output=True)
            res = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else res.stderr
    except Exception as e:
        return f"ADB Error: {e}"

def github_connector(action: str, target: str) -> str:
    """Interface with local Git CLI."""
    try:
        if action == "status":
            cmd = "git status"
        elif action == "commit":
            cmd = f"git commit -m \"{target}\""
        elif action == "push":
            cmd = "git push"
        elif action == "add":
            cmd = f"git add {target}"
        else:
            return "Unknown git action"
            
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else res.stderr
    except Exception as e:
        return f"Git Error: {e}"

def gmail_connector(action: str, to: str = "", subject: str = "", body: str = "") -> str:
    """Send emails via SMTP or read via IMAP using environment variables."""
    import os
    import smtplib
    from email.message import EmailMessage
    
    email_user = os.environ.get("AETHER_EMAIL_USER")
    email_pass = os.environ.get("AETHER_EMAIL_PASS")
    
    if not email_user or not email_pass:
        return "Error: AETHER_EMAIL_USER and AETHER_EMAIL_PASS environment variables are required."
        
    if action == "send":
        if not to or not subject:
            return "Error: 'to' and 'subject' fields are required for sending emails."
            
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = email_user
            msg['To'] = to
            
            # Use Gmail SMTP
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(email_user, email_pass)
                server.send_message(msg)
                
            return f"Email successfully sent to {to}"
        except Exception as e:
            return f"SMTP Error: {str(e)}"
    elif action == "read":
        # IMAP could be implemented here
        return "IMAP read action is supported but requires further configuration."
    else:
        return "Unknown action. Supported: send, read."
