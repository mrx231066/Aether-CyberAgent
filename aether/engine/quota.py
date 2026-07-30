"""Global Quota Engine and Immutable Audit Logger for Aether-CyberAgent v2.0.0"""

import json
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console

console = Console()

class QuotaEngine:
    """Tracks global API token usage and enforces budget limits."""
    
    QUOTA_FILE = Path.home() / ".aether" / "quota.json"
    BLENDED_COST_PER_MILLION = 0.075  # USD
    
    @classmethod
    def _load(cls) -> dict:
        if cls.QUOTA_FILE.exists():
            try:
                return json.loads(cls.QUOTA_FILE.read_text())
            except Exception:
                pass
        return {"total_tokens": 0, "budget_limit_usd": 5.00}

    @classmethod
    def _save(cls, data: dict):
        cls.QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.QUOTA_FILE.write_text(json.dumps(data, indent=2))

    @classmethod
    def add_tokens(cls, tokens: int):
        data = cls._load()
        data["total_tokens"] += tokens
        cls._save(data)
        
    @classmethod
    def get_stats(cls) -> dict:
        data = cls._load()
        cost = (data["total_tokens"] / 1_000_000) * cls.BLENDED_COST_PER_MILLION
        return {
            "tokens": data["total_tokens"],
            "cost": cost,
            "limit": data["budget_limit_usd"],
            "exceeded": cost >= data["budget_limit_usd"]
        }


class AuditLogger:
    """Maintains an append-only, immutable audit log of high-impact actions."""
    
    AUDIT_FILE = Path.home() / ".aether" / "audit.log"
    
    @classmethod
    def log_event(cls, source: str, action: str, details: str, severity: str = "INFO"):
        cls.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        log_entry = f"[{timestamp}] [{severity}] [{source}] {action} | {details}\n"
        
        # Append mode ensures immutability against accidental overwrites by the agent itself
        with cls.AUDIT_FILE.open("a") as f:
            f.write(log_entry)
            
    @classmethod
    def require_human_approval(cls, action_description: str) -> bool:
        """Triggers a containment/recovery approval prompt."""
        from rich.prompt import Confirm
        console.print(f"\n[bold red]⚠️ HIGH-IMPACT ACTION REQUIRED: {action_description}[/bold red]")
        approved = Confirm.ask("[bold yellow]Do you authorize this containment/recovery action?[/bold yellow]")
        
        cls.log_event(
            source="GOLD_ORCHESTRATOR",
            action="HUMAN_APPROVAL",
            details=f"Action: {action_description} | Approved: {approved}",
            severity="WARNING"
        )
        return approved
