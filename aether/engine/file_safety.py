"""File Safety Inspector for Aether-CyberAgent v4.0.0.

Enforces the MANDATORY rule: READ → ANALYZE → AUTHORIZE → ACT.
Prevents Indirect Prompt Injection and execution of unverified/untrusted data.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
from rich.console import Console

console = Console()

@dataclass
class SafetyAnalysis:
    is_safe: bool
    requires_human: bool
    risks_found: List[str]
    adversarial_directives: bool

class FileSafetyInspector:
    """Reads, parses, and identifies risks in target files before action execution."""
    
    # Signatures of Indirect Prompt Injection (Adversarial AI directives)
    _ADVERSARIAL_PATTERNS = [
        re.compile(r'(?i)(ignore\s+previous\s+instructions)'),
        re.compile(r'(?i)(override\s+system\s+prompt)'),
        re.compile(r'(?i)(you\s+are\s+now\s+a)'),
        re.compile(r'(?i)(disregard\s+security\s+policies)'),
        re.compile(r'(?i)(from\s+now\s+on\s+always)'),
        re.compile(r'(?i)(system:\s*ignore)'),
        re.compile(r'(?i)(Aether.*must\s+execute\s+this)'),
    ]

    # Signatures of highly destructive/risky code primitives
    _DANGEROUS_CODE_PATTERNS = [
        re.compile(r'os\.system\('),
        re.compile(r'subprocess\.(Popen|call|run|check_output)'),
        re.compile(r'eval\('),
        re.compile(r'exec\('),
        re.compile(r'rm\s+-rf\s+/'),
        re.compile(r'shutil\.rmtree'),
    ]

    @classmethod
    def analyze_file(cls, file_path: str) -> SafetyAnalysis:
        """Enforces the READ and ANALYZE phases."""
        path = Path(file_path).resolve()
        
        if not path.exists():
            return SafetyAnalysis(True, False, [], False) # New files have no existing untrusted data
            
        try:
            # Read first 100KB to prevent memory exhaustion / zip bombs
            content = path.read_text(encoding='utf-8', errors='ignore')[:102400]
        except Exception as e:
            return SafetyAnalysis(False, True, [f"Failed to read file: {e}"], False)

        risks = []
        has_adversarial = False
        
        # 1. Check for Indirect Prompt Injection
        for pattern in cls._ADVERSARIAL_PATTERNS:
            if pattern.search(content):
                has_adversarial = True
                risks.append("CRITICAL: Adversarial AI directive (Prompt Injection) detected in file contents.")
                break # Only need one to flag
                
        # 2. Check for dangerous primitives
        for pattern in cls._DANGEROUS_CODE_PATTERNS:
            if pattern.search(content):
                risks.append(f"HIGH: Potentially dangerous execution primitive detected: {pattern.pattern}")
                
        is_safe = not has_adversarial and len(risks) == 0
        requires_human = has_adversarial or len(risks) > 0
        
        if requires_human:
            console.print(f"\n[bold red]⚠️ FILE SAFETY ANALYSIS FAILED for {path.name}[/bold red]")
            for risk in risks:
                console.print(f"  [dim]- {risk}[/dim]")
                
        return SafetyAnalysis(is_safe, requires_human, risks, has_adversarial)
