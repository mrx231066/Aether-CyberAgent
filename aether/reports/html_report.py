"""HTML Report Generator for Aether-CyberAgent v2.0.0.

Generates rich, standalone HTML security reports using Jinja2 templates.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

console = Console()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aether-CyberAgent Security Report</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --accent: #58a6ff;
            --green: #3fb950;
            --red: #f85149;
            --yellow: #d29922;
            --purple: #bc8cff;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: var(--bg); color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            padding: 2rem; line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            text-align: center; padding: 2rem; margin-bottom: 2rem;
            border: 1px solid var(--border); border-radius: 12px;
            background: var(--card-bg);
        }
        header h1 { color: var(--accent); font-size: 2rem; }
        header .subtitle { color: #8b949e; margin-top: 0.5rem; }
        .metrics {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        .metric-card {
            background: var(--card-bg); border: 1px solid var(--border);
            border-radius: 8px; padding: 1.5rem; text-align: center;
        }
        .metric-card .value {
            font-size: 2.5rem; font-weight: bold; color: var(--accent);
        }
        .metric-card .label { color: #8b949e; font-size: 0.9rem; }
        .metric-card.critical .value { color: var(--red); }
        .metric-card.success .value { color: var(--green); }
        .metric-card.warning .value { color: var(--yellow); }
        .section {
            background: var(--card-bg); border: 1px solid var(--border);
            border-radius: 8px; margin-bottom: 1.5rem; overflow: hidden;
        }
        .section-header {
            padding: 1rem 1.5rem; border-bottom: 1px solid var(--border);
            font-weight: 600; font-size: 1.1rem;
        }
        .section-body { padding: 1.5rem; }
        table { width: 100%; border-collapse: collapse; }
        th, td {
            padding: 0.75rem 1rem; text-align: left;
            border-bottom: 1px solid var(--border);
        }
        th { color: #8b949e; font-weight: 500; font-size: 0.85rem; text-transform: uppercase; }
        .severity-critical { color: var(--red); font-weight: bold; }
        .severity-high { color: #ff7b72; }
        .severity-medium { color: var(--yellow); }
        .severity-low { color: var(--green); }
        .badge {
            display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
            font-size: 0.75rem; font-weight: 600;
        }
        .badge-pass { background: #238636; color: white; }
        .badge-fail { background: #da3633; color: white; }
        code {
            background: #0d1117; padding: 0.2rem 0.4rem; border-radius: 4px;
            font-family: 'Fira Code', 'Cascadia Code', monospace; font-size: 0.85rem;
        }
        pre {
            background: #0d1117; padding: 1rem; border-radius: 8px;
            overflow-x: auto; font-size: 0.85rem;
        }
        footer {
            text-align: center; color: #8b949e; padding: 2rem; font-size: 0.85rem;
        }
        .team-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 6px; }
        .team-blue { background: #58a6ff; }
        .team-red { background: #f85149; }
        .team-yellow { background: #d29922; }
        .team-purple { background: #bc8cff; }
        .team-green { background: #3fb950; }
        .team-gold { background: #f0c000; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🛡️ AETHER-CYBERAGENT</h1>
        <div class="subtitle">Autonomous Multi-Agent AI Security Report</div>
        <div class="subtitle">Generated: {{ timestamp }} | v2.0.0</div>
    </header>

    <div class="metrics">
        <div class="metric-card">
            <div class="value">{{ files_scanned }}</div>
            <div class="label">Files Scanned</div>
        </div>
        <div class="metric-card critical">
            <div class="value">{{ vulnerabilities_found }}</div>
            <div class="label">Vulnerabilities Found</div>
        </div>
        <div class="metric-card success">
            <div class="value">{{ vulnerabilities_fixed }}</div>
            <div class="label">Auto-Patched</div>
        </div>
        <div class="metric-card warning">
            <div class="value">{{ failed_patches }}</div>
            <div class="label">Failed Patches</div>
        </div>
        <div class="metric-card">
            <div class="value">{{ "%.1f"|format(duration) }}s</div>
            <div class="label">Scan Duration</div>
        </div>
        <div class="metric-card {{ 'success' if success else 'critical' }}">
            <div class="value">{{ "PASS" if success else "FAIL" }}</div>
            <div class="label">Overall Status</div>
        </div>
    </div>

    {% if verified_patches %}
    <div class="section">
        <div class="section-header">
            <span class="team-indicator team-green"></span>
            ✅ Verified Patches ({{ verified_patches|length }})
        </div>
        <div class="section-body">
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Vulnerability</th>
                        <th>Severity</th>
                        <th>Attempts</th>
                        <th>Z3</th>
                        <th>Hypothesis</th>
                    </tr>
                </thead>
                <tbody>
                    {% for patch in verified_patches %}
                    <tr>
                        <td><code>{{ patch.file.split('/')[-1] }}</code></td>
                        <td>{{ patch.vulnerability_title }}</td>
                        <td class="severity-{{ patch.severity|lower }}">{{ patch.severity }}</td>
                        <td>{{ patch.attempts }}</td>
                        <td><span class="badge badge-pass">{{ patch.verification.z3 }}</span></td>
                        <td><span class="badge badge-pass">{{ patch.verification.hypothesis }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    {% if failed_patches %}
    <div class="section">
        <div class="section-header">
            <span class="team-indicator team-red"></span>
            ❌ Failed Patches ({{ failed_patches|length }})
        </div>
        <div class="section-body">
            <table>
                <thead>
                    <tr><th>File</th><th>Reason</th></tr>
                </thead>
                <tbody>
                    {% for patch in failed_patches %}
                    <tr>
                        <td><code>{{ patch.file.split('/')[-1] }}</code></td>
                        <td>{{ patch.reason }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    {% if red_team_vectors %}
    <div class="section">
        <div class="section-header">
            <span class="team-indicator team-red"></span>
            🔴 Red Team Attack Vectors ({{ red_team_vectors|length }})
        </div>
        <div class="section-body">
            <table>
                <thead>
                    <tr><th>Type</th><th>File</th><th>Line</th><th>Severity</th><th>Description</th></tr>
                </thead>
                <tbody>
                    {% for v in red_team_vectors %}
                    <tr>
                        <td><code>{{ v.vector_type }}</code></td>
                        <td><code>{{ v.target.split('/')[-1] }}</code></td>
                        <td>{{ v.line_number }}</td>
                        <td class="severity-{{ v.severity|lower }}">{{ v.severity }}</td>
                        <td>{{ v.description }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    {% if state_log %}
    <div class="section">
        <div class="section-header">
            <span class="team-indicator team-gold"></span>
            📈 Pipeline Event Log ({{ state_log|length }} events)
        </div>
        <div class="section-body">
            <table>
                <thead>
                    <tr><th>Timestamp</th><th>Event</th><th>Phase</th><th>Details</th></tr>
                </thead>
                <tbody>
                    {% for event in state_log[-20:] %}
                    <tr>
                        <td><code>{{ event.timestamp[:19] }}</code></td>
                        <td>{{ event.event }}</td>
                        <td>{{ event.phase }}</td>
                        <td>{{ event.get('file', event.get('error', ''))[:60] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    <footer>
        Built with 🛡️ by Aether Security Team — Deterministic Defense. Probabilistic Intelligence. Autonomous Resilience.
    </footer>
</div>
</body>
</html>"""


class HtmlReporter:
    """Generates standalone HTML security reports."""

    def generate_report(self, pipeline_result: Any, red_team_report: Any = None) -> str:
        """Generate an HTML report from pipeline results.

        Args:
            pipeline_result: The PipelineResult from the Gold Team.
            red_team_report: Optional RedTeamReport for attack surface data.

        Returns:
            Rendered HTML string.
        """
        from jinja2 import Template

        template = Template(HTML_TEMPLATE)

        red_vectors = []
        if red_team_report and hasattr(red_team_report, "vectors"):
            red_vectors = [
                {
                    "vector_type": v.vector_type,
                    "target": v.target,
                    "line_number": v.line_number,
                    "severity": v.severity,
                    "description": v.description,
                }
                for v in red_team_report.vectors
            ]

        context = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "files_scanned": getattr(pipeline_result, "files_scanned", 0),
            "vulnerabilities_found": getattr(pipeline_result, "vulnerabilities_found", 0),
            "vulnerabilities_fixed": getattr(pipeline_result, "vulnerabilities_fixed", 0),
            "failed_patches": len(getattr(pipeline_result, "failed_patches", [])),
            "duration": getattr(pipeline_result, "scan_duration", 0.0),
            "success": getattr(pipeline_result, "success", True),
            "verified_patches": getattr(pipeline_result, "verified_patches", []),
            "failed_patches_list": getattr(pipeline_result, "failed_patches", []),
            "state_log": getattr(pipeline_result, "state_log", []),
            "red_team_vectors": red_vectors,
        }

        return template.render(**context)

    def save_report(self, html_content: str, output_dir: str) -> str:
        """Save the HTML report to disk.

        Args:
            html_content: Rendered HTML string.
            output_dir: Directory to save the report in.

        Returns:
            Path to the saved report file.
        """
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = dir_path / f"aether_report_{timestamp}.html"
        output_path.write_text(html_content, encoding="utf-8")

        console.print(f"[bold green]📄 HTML report saved: {output_path}[/bold green]")
        return str(output_path)

    def export_from_pipeline(self, pipeline_result: Any, output_dir: str,
                              red_team_report: Any = None) -> str:
        """Generate and save the report, returning the file path."""
        html = self.generate_report(pipeline_result, red_team_report)
        return self.save_report(html, output_dir)
