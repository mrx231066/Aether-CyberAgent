"""Policy and Privacy Engines for Aether-CyberAgent v2.0.0"""

import re
from enum import Enum
from typing import Dict, Any, Tuple
from rich.console import Console

console = Console()

class PolicyOutcome(Enum):
    ALLOW = "ALLOW"
    ALLOW_AND_AUDIT = "ALLOW_AND_AUDIT"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    DENY = "DENY"

class PolicyEngine:
    """Evaluates requested actions against the system security policy."""
    
    # Map actions to baseline policies
    _POLICY_MAP = {
        "read_file": PolicyOutcome.ALLOW,
        "run_linter": PolicyOutcome.ALLOW,
        "run_sast": PolicyOutcome.ALLOW_AND_AUDIT,
        "generate_patch": PolicyOutcome.ALLOW,
        "apply_patch": PolicyOutcome.APPROVAL_REQUIRED, # Can be downgraded by YOLO
        "delete_file": PolicyOutcome.APPROVAL_REQUIRED,
        "execute_shell": PolicyOutcome.APPROVAL_REQUIRED,
        "modify_infrastructure": PolicyOutcome.APPROVAL_REQUIRED,
        "access_credentials": PolicyOutcome.DENY,
        "attack_external": PolicyOutcome.DENY,
        "exfiltrate_data": PolicyOutcome.DENY
    }

    @classmethod
    def evaluate(cls, action: str, file_path: str = None, yolo_enabled: bool = False, is_reversible: bool = True) -> PolicyOutcome:
        """Evaluates an action and strictly enforces READ -> ANALYZE -> AUTHORIZE."""
        outcome = cls._POLICY_MAP.get(action, PolicyOutcome.APPROVAL_REQUIRED)
        
        # MANDATORY RULE: If action involves a file, we MUST analyze it first.
        # This prevents execution or blind modification of untrusted prompt-injected data.
        if file_path and action in ("apply_patch", "execute_shell", "run_sast", "modify_infrastructure"):
            from aether.engine.file_safety import FileSafetyInspector
            analysis = FileSafetyInspector.analyze_file(file_path)
            
            if analysis.requires_human:
                console.print(f"[bold red]🚫 POLICY ENGINE: YOLO mode disabled for {file_path} due to safety risks.[/bold red]")
                return PolicyOutcome.APPROVAL_REQUIRED
        
        # YOLO Mode overrides for safe/reversible operations (only if file passed safety analysis above)
        if yolo_enabled and outcome == PolicyOutcome.APPROVAL_REQUIRED:
            if action in ("apply_patch", "execute_shell") and is_reversible:
                return PolicyOutcome.ALLOW_AND_AUDIT
                
        return outcome

class PrivacyEngine:
    """Local-first privacy enforcer. Sanitizes outbound prompts."""
    
    # Patterns for secrets that must never leave the local environment
    _SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|secret|token|password)[\s:=]+[\'"]?([a-zA-Z0-9\-_]{16,})[\'"]?', '<REDACTED_SECRET>'),
        (r'sk-[a-zA-Z0-9]{20,}', '<REDACTED_OPENAI_KEY>'),
        (r'ghp_[a-zA-Z0-9]{36,}', '<REDACTED_GITHUB_PAT>'),
        (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', '<REDACTED_JWT>')
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return text
            
        sanitized = text
        for pattern, replacement in cls._SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
            
        # Entropy checks could also be hooked here to block high-entropy blobs
        return sanitized
