# Aether-CyberAgent Architecture v2.0.0

## System Overview and Design Philosophy
Aether-CyberAgent is an Autonomous Multi-Agent AI Security Platform designed to continuously monitor, analyze, and repair security vulnerabilities within software systems. The philosophy centers around a self-healing, closed-loop approach utilizing specialized AI agents (teams) working in orchestration to simulate both adversarial and defensive postures.

## Team Implementations

### Blue Team
Focuses on defensive analysis and monitoring. It continuously analyzes code bases using Python AST parsing to detect potential vulnerabilities (eval/exec, shell injection, deserialization, hardcoded secrets) and misconfigurations before they can be exploited.

### Red Team (New in v2.0.0)
Active attack surface enumeration agent. Performs non-destructive reconnaissance including endpoint discovery from web frameworks (Flask/FastAPI/Django), auth bypass detection, SQL injection pattern matching, SSRF/IDOR scanning, entropy-based secret detection (Shannon entropy > 4.5), and dangerous default configuration analysis. Produces attack surface scores and actionable recommendations.

### Yellow Team
Responsible for autonomous code generation and remediation. Uses Google Gemini with function calling to plan solutions, write code, execute commands, and invoke tools autonomously. Handles both interactive REPL conversations and automated patch generation.

### Purple Team
Bridges the gap between offensive and defensive analysis. Verifies patches mathematically using Z3 SMT Solver for constraint checking and Hypothesis for property-based boundary testing. Confirms if vulnerabilities are addressed and if fixes maintain code correctness.

### Gold Team
The core orchestration and autonomic engine. Coordinates the actions of all other teams, manages the lifecycle of a scan, and implements the self-healing loop — if verification fails, it intercepts the failure trace, updates context, and retries up to 3 times.

### Green Team
The tool execution engine. Executes scripts and shell commands in isolated sandboxes with strict timeouts. Supports Docker-based isolation when available, with fallback to local execution.

### White Team
Focuses on governance and reporting. Generates SARIF v2.1.0 JSON reports for CI/CD ingestion and rich standalone HTML reports with metrics dashboards, patch visualization, and attack vector tables.

### Silver Team
Real-time ethical guardian daemon. Monitors active sessions for malicious intents or dangerous boundary violations, purging dangerous context when detected.

## Data Flow Diagram
```text
[Source Code/Environment]
         │
         ▼
┌─────────────────────┐
│  🔵 Blue Team       │──── AST Audit ────┐
│  (Static Analysis)  │                    │
└─────────────────────┘                    │
         │                                  │
         ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐
│  🔴 Red Team        │          │  🟡 Yellow Team     │
│  (Attack Surface)   │          │  (AI Remediation)   │
└─────────────────────┘          └──────────┬──────────┘
         │                                  │
         │                                  ▼
         │                       ┌─────────────────────┐
         │                       │  🟣 Purple Team     │
         │                       │  (Z3 + Hypothesis)  │
         │                       └──────────┬──────────┘
         │                                  │
         │                    ❌ FAIL ───────┤
         │                    │              │ ✅ PASS
         │                    ▼              ▼
         │          ┌─────────────────┐   ┌─────────────────┐
         │          │  🥇 Gold Team   │   │  🟢 Green Team  │
         │          │  (Retry Loop)   │   │  (Sandbox Exec) │
         │          └─────────────────┘   └────────┬────────┘
         │                                         │
         └────────────────────┬────────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │  ⚪ White Team      │
                    │  SARIF + HTML       │
                    │  Reports            │
                    └─────────────────────┘
```

## Technology Choices and Rationale
- **Python 3.11+**: Selected for its rich ecosystem in both AI (google-genai) and security tooling.
- **Typer & Rich**: Robust, user-friendly CLI with rich terminal rendering.
- **Streamlit**: Quick interactive web dashboards for data visualization.
- **Docker**: Sandboxing and isolated execution of scans and remediations.
- **z3-solver & networkx**: Constraint solving and graph analysis for deep structural and logic analysis.
- **Pydantic**: Rigorous data validation and typing across agent communications.
- **watchdog**: Filesystem monitoring for watch mode.
- **Jinja2**: HTML report template rendering.

## Plugin Architecture (New in v2.0.0)
Aether supports hot-loadable plugins from `~/.aether/plugins/`:
1. **Single-file plugins** (`.py` files with `PLUGIN_META` dict and `register()` function)
2. **Package plugins** (directories with `__init__.py`)
3. **Hook types**: Tools, slash commands, and custom scanner hooks

## Self-Healing Loop Algorithm
1. **Discover**: Blue Team scans and identifies potential issues via AST parsing.
2. **Enumerate**: Red Team maps the attack surface and identifies exploitable vectors.
3. **Verify**: Purple team validates findings with Z3 solver and Hypothesis testing.
4. **Plan**: Gold team prioritizes the verified issue and tasks the Yellow team.
5. **Remediate**: Yellow team generates a patch via Gemini AI.
6. **Test**: The fix is verified by Purple team and executed in Green team sandbox.
7. **Report**: White team exports SARIF + HTML reports for governance.
8. **Retry**: If verification fails, Gold team intercepts and retries with updated context (max 3 attempts).
