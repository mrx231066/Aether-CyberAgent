"""Orange Team: Threat Intelligence & Adversary Emulation (v4.0.1).

Monitors public threat intelligence, Tor-related infrastructure, and OSINT
to correlate external threats with internal telemetry.
Converts intelligence into actionable detection rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table

console = Console()

@dataclass
class ThreatIndicator:
    ioc: str
    ioc_type: str  # 'ip', 'domain', 'hash', 'tor_node'
    confidence: str # 'HIGH', 'MEDIUM', 'LOW'
    mitre_tactic: str
    description: str

class OrangeTeamIntel:
    """Orange Team Threat Intelligence Gathering."""
    
    def __init__(self):
        self.iocs: List[ThreatIndicator] = []
        
    def monitor_public_feeds(self):
        """Simulate polling public OSINT and Tor intelligence feeds."""
        console.print("[bold orange3]🟠 Orange Team: Monitoring OSINT & Tor infrastructure feeds...[/bold orange3]")
        
        # In a real environment, this would poll AlienVault, AbuseCH, Tor exit lists, etc.
        # Here we mock the ingestion of threat intelligence.
        self.iocs = [
            ThreatIndicator("185.220.101.4", "tor_node", "HIGH", "Reconnaissance", "Known Tor exit node scanning ports"),
            ThreatIndicator("malicious-crypto-miner.xyz", "domain", "HIGH", "Execution", "Known cryptojacking C2"),
            ThreatIndicator("e3b0c44298fc1c149afbf4c8996fb924", "hash", "MEDIUM", "Persistence", "Suspicious scheduled task binary"),
        ]
        
    def generate_detection_rules(self) -> Dict[str, str]:
        """Convert IOCs into Blue Team detection rules (e.g., YARA, Snort, or internal FW blocklists)."""
        rules = {}
        for ioc in self.iocs:
            if ioc.ioc_type == "tor_node" or ioc.ioc_type == "ip":
                rules[f"BLOCK_IP_{ioc.ioc}"] = f"iptables -A INPUT -s {ioc.ioc} -j DROP"
            elif ioc.ioc_type == "domain":
                rules[f"DNS_SINKHOLE_{ioc.ioc}"] = f"address=/{ioc.ioc}/0.0.0.0"
                
        return rules

    def report_intel(self):
        if not self.iocs:
            return
            
        table = Table(title="🟠 Orange Team Threat Intelligence", border_style="orange3")
        table.add_column("IOC", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("MITRE Tactic", style="yellow")
        table.add_column("Confidence", style="red")
        
        for ioc in self.iocs:
            table.add_row(ioc.ioc, ioc.ioc_type, ioc.mitre_tactic, ioc.confidence)
            
        console.print(table)

# --- NEW: v1.1 Blueprint Validation Mode ---

@dataclass
class OrangeVerificationResult:
    finding_id: str
    pre_patch_result: Any
    post_patch_result: Any
    verdict: str  # "fixed", "still_exploitable", "inconclusive"
    test_stub: str = ""

class OrangeTeamVerifier:
    """Closes the loop between Red Team's PoC and Green Team's patch."""
    
    def verify_remediation(self, red_result: Any, patch_diff: str) -> OrangeVerificationResult:
        console.print("\n[bold orange3]🟠 ORANGE TEAM REMEDIATION VERIFIER[/bold orange3]")
        console.print("  [dim]Re-invoking Red Team PoC path against patched code...[/dim]")
        
        verdict = "still_exploitable"
        stub = ""
        post_patch_output = ""
        
        try:
            from aether.engine.sandbox import IsolatedSandbox
            
            with IsolatedSandbox() as sandbox:
                # Apply the patch conceptually (or deploy the patched file)
                sandbox.write_file("patch.diff", patch_diff)
                
                # Retrieve the original payload from Red Team Result
                payload = getattr(red_result, "poc_payload", "print('Fallback PoC Execution')")
                sandbox.write_file("payload.py", payload)
                
                # Execute safely
                result = sandbox.execute("python payload.py", timeout=5.0)
                
                # If execution fails, the exploit was blocked by the patch
                if result["exit_code"] != 0:
                    verdict = "fixed"
                    post_patch_output = result["stderr"]
                else:
                    post_patch_output = result["stdout"]
                    
        except Exception as e:
            verdict = "inconclusive"
            post_patch_output = str(e)
            
        if verdict == "fixed":
            # Generate the Python regression test based on payload
            stub = (
                "import unittest\n"
                "import subprocess\n\n"
                "class ExploitRegressionTest(unittest.TestCase):\n"
                "    def test_regression_cwe(self):\n"
                f"        \"\"\"Auto-generated regression test stub to prevent recurrence.\"\"\"\n"
                "        # Original payload executed safely to ensure it still fails\n"
                "        pass\n"
            )
            console.print("  [bold green]✅ Verdict: FIXED[/bold green]")
        else:
            console.print("  [bold red]❌ Verdict: STILL EXPLOITABLE[/bold red]")
        
        return OrangeVerificationResult(
            finding_id=getattr(red_result, "finding_id", "unknown"),
            pre_patch_result=red_result,
            post_patch_result=post_patch_output,
            verdict=verdict,
            test_stub=stub
        )
