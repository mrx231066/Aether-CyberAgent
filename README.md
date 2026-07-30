<div align="center">

# 🛡️ AETHER-CYBERAGENT

### Autonomous Multi-Agent AI Security Platform & Terminal Co-Pilot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-AI_Powered-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![SARIF](https://img.shields.io/badge/SARIF-v2.1.0-orange?style=for-the-badge)](https://sarifweb.azurewebsites.net/)
[![PyPI](https://img.shields.io/badge/PyPI-aether--cyberagent-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/aether-cyberagent/)
[![Version](https://img.shields.io/badge/Version-2.0.0-red?style=for-the-badge)]()

**Deterministic Computer Science × Probabilistic AI**

*AST Parsing · Graph Theory · Formal Logic · Google Gemini · Self-Healing Loops · Red Team Recon · Interactive REPL*

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [Usage](#-usage) · [New in v2.0.0](#-new-in-v200) · [Dashboard](#-dashboard) · [Contributing](#-contributing)

---

</div>

## 🧬 What is Aether-CyberAgent?

**Aether-CyberAgent** is an elite, autonomous, multi-agent AI security platform and terminal co-pilot. It fuses **deterministic computer science** (AST parsing, graph theory, formal logic) with **probabilistic AI** (Google Gemini function calling) to create a **self-healing, autonomic software engine**.

Version 2.0.0 introduces the **Red Team Agent**, **Plugin System**, **HTML Security Reports**, **Watch Mode**, and **Entropy-Based Secret Scanning** — making Aether a complete offensive + defensive security powerhouse.

---

## 🆕 New in v2.0.0

### 🔴 Red Team Agent
Active attack surface enumeration — endpoint discovery, auth bypass detection, SQL injection patterns, SSRF/IDOR scanning, entropy-based secret detection, and dangerous default analysis.

### 📦 Plugin System
Hot-loadable plugins from `~/.aether/plugins/` with runtime registration of custom tools, commands, and scanner hooks.

### 📄 HTML Security Reports
Rich standalone HTML reports with dark theme, metrics dashboard, patch visualization, and attack vector tables.

### 🔄 Watch Mode
`aether watch .` — continuous filesystem monitoring with debounced auto-scanning on file changes.

### 🔑 Enhanced Secret Scanner
Shannon entropy analysis for detecting API keys, JWTs, and base64 secrets — not just variable name matching.

---

## ✨ Key Features

- 💬 **Interactive Agent REPL** — Converse with Aether dynamically in a rich terminal interface.
- 🛠️ **Autonomous Tool Execution** — Aether can read/write files and execute shell scripts safely.
- 🔄 **Self-Correction Loop** — If a script fails, the Gold Team intercepts stderr and auto-fixes (up to 3 retries).
- 🔍 **Deterministic Vulnerability Detection** — Python AST-based scanning, not regex guessing.
- 🧠 **AI-Powered Remediation** — Google Gemini generates type-annotated, secure code patches.
- 📐 **Mathematical Verification** — Z3 SMT Solver proves correctness, Hypothesis fuzzes edge cases.
- 🔴 **Red Team Recon** — Active attack surface enumeration and CVSS scoring.
- 📊 **Live Dashboard** — Real-time Streamlit visualization of the security pipeline.
- 📋 **SARIF v2.1.0 Reports** — Native GitHub Security tab integration.
- 📄 **HTML Reports** — Standalone visual security reports.
- 🔌 **Plugin System** — Extend Aether with custom tools and scanners.

---

## 🏛️ Architecture

Aether-CyberAgent implements a **full 9-Team Cybersecurity Spectrum** model:

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     🥇 GOLD TEAM (Orchestrator)                      │
│              Autonomic Self-Healing Loop · Max 3 Retries             │
│                                                                      │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐  │
│  │ 🔵 BLUE    │──▶│ 🔴 RED     │──▶│ 🟡 YELLOW  │──▶│ 🟢 GREEN   │  │
│  │ AST Audit  │   │ Sandbox    │   │ AI Patch   │   │ Tool Run   │  │
│  │ + GraphRAG │   │ Validation │   │ + Scripts  │   │ + Sandbox  │  │
│  └────────────┘   └─────▲──────┘   └─────┬──────┘   └─────┬──────┘  │
│                         │                │                │         │
│  ┌────────────┐         │      ┌─────────▼────────┐       │         │
│  │ 🟠 ORANGE  │─────────┘      │ 🟣 PURPLE        │       │         │
│  │ Intel &    │                │ Z3 Verify        │       │         │
│  │ Verifier   │                │ + Hypothesis     │       │         │
│  └────────────┘                └─────────┬────────┘       │         │
│                                          │                │         │
│                                 ❌ FAIL ─┴───────────────┐│         │
│                                                          ▼▼         │
│                                                    ┌────────────┐   │
│                                                    │ ⚪ WHITE   │   │
│                                                    │ SARIF+HTML │   │
│                                                    │ + Reports  │   │
│                                                    └────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

| Team | Role | Mechanism |
|:----:|------|-----------|
| 🔵 **Blue Team** | Static Auditor | AST-based vulnerability detection (SQLi, eval/exec, deserialization) |
| 🔴 **Red Team** | Adversarial Simulator | Confirms Blue Team findings using isolated, strictly-sandboxed PoCs |
| 🟡 **Yellow Team** | Autonomous Developer | Google Gemini function calling, script generation, patch logic |
| 🟢 **Green Team** | Tool Execution Engine | Sandboxed script/shell execution via Docker |
| 🟠 **Orange Team** | Remediation Verifier | Threat intel ingestion & closing the loop on patched PoC execution |
| 🟣 **Purple Team** | Formal Verification | Z3 SMT Solver + Hypothesis property-based boundary testing |
| 🥇 **Gold Team** | Autonomic Orchestrator | Self-correction loop — intercepts failures, retries with updated context |
| ⚪ **White Team** | Governance & Reporting | SARIF v2.1.0 + HTML reports for CI/CD ingestion |
| 🛡️ **Silver Team** | Guardian Daemon | Real-time ethical daemon, audit logging, and payload constraint enforcement |

---

## 🔒 Responsible Use

Aether is a **defensive security orchestration tool**. To prevent misuse:
- **Red Team operations are strictly sandboxed:** The Red Team operates *only* against existing local Blue Team findings, executing stubbed validation payloads inside isolated Docker containers. It is never used as an open-ended "exploit generation" tool against external targets.
- **Self-Updating is strictly gated:** Aether checks a hardcoded, official GitHub URL for updates to prevent malicious fork injection, and **never** applies an update without explicit human confirmation.

- **Nuitka is a tamper deterrent, not a security boundary:** Native compilation protects the distributed binary from casual modification, but if the source code is public, Nuitka alone does not guarantee execution safety. Rely on Docker and the Pre-Execution Guard for actual sandboxing.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker** (optional, for sandbox execution)
- **Google Gemini API Key** ([Get one free](https://aistudio.google.com/apikey))

### Installation

```bash
# From PyPI
pip install aether-cyberagent

# From source
git clone https://github.com/mrx231066/Aether-CyberAgent.git
cd Aether-CyberAgent
pip install -e ".[all]"
```

---

## 💡 Usage

### Launch Interactive Agent REPL

```bash
aether
```

### Run Full Security Scan (Blue + Red + AI Patch + Verify)

```bash
aether scan .
aether scan ./src --max-retries 5 --verbose
```

### Run Red Team Attack Surface Enumeration

```bash
aether redscan .
aether redscan ./my_app
```

### Watch Mode (Auto-Scan on File Changes)

```bash
aether watch .
aether watch ./src --debounce 5.0
```

### List Plugins

```bash
aether plugins
```

### Launch Visual Dashboard

```bash
aether dashboard
```

### Verify a Specific File

```bash
aether verify ./src/module.py
```

### Supported Slash Commands (REPL)

| Command | Description |
|---------|-------------|
| `/help` | Command reference |
| `/scan [path]` | Full multi-agent security scan |
| `/redscan [path]` | Red Team attack surface scan |
| `/model` | Switch Gemini model |
| `/auth` | Update API key |
| `/status` | Session state & graph metrics |
| `/quota` | Token usage & cost |
| `/run <script>` | Execute script in sandbox |
| `/plugins` | List loaded plugins |
| `/theme <name>` | Switch UI theme |
| `/rollback <n>` | Rollback n turns |
| `/branch <name>` | Fork session history |
| `/clear` | Clear terminal |
| `/exit` | Close REPL |

---

## 📁 Project Structure (v2.0.0)

```text
aether-cyberagent/
├── aether/
│   ├── ai/
│   │   ├── gemini_client.py       # Dynamic model discovery & Structured Output
│   │   ├── local_llm.py           # Ollama local LLM client
│   │   ├── prompt_builder.py      # Tiered system prompt constructor
│   │   ├── router.py              # Hybrid LLM router (cloud/local)
│   │   └── providers/             # Unified AI provider protocol
│   ├── agents/
│   │   ├── blue_auditor.py        # Static AST vulnerability parser
│   │   ├── red_attacker.py        # 🆕 Attack surface enumeration agent
│   │   ├── yellow_patcher.py      # AI developer & script generator
│   │   ├── purple_verifier.py     # Z3 formal logic & property testing
│   │   ├── gold_autonomic.py      # Self-correction execution loop
│   │   ├── silver_guardian.py     # Ethical boundary daemon
│   │   └── master_router.py       # Swarm dispatch
│   ├── engine/
│   │   ├── tools.py               # Autonomous tool execution engine
│   │   ├── graph_memory.py        # NetworkX dependency graph
│   │   ├── graph_rag.py           # SQLite-cached GraphRAG
│   │   ├── sandbox.py             # Docker runner
│   │   ├── watcher.py             # 🆕 Watch mode with watchdog
│   │   ├── plugins.py             # 🆕 Hot-loadable plugin system
│   │   ├── connectors.py          # ADB + Git connectors
│   │   ├── shell_translator.py    # NL-to-shell translation
│   │   └── ...
│   ├── reports/
│   │   ├── sarif.py               # White team SARIF v2.1.0 exporter
│   │   └── html_report.py         # 🆕 Standalone HTML report generator
│   ├── dashboard/
│   │   └── app.py                 # Streamlit visualizer
│   ├── web/
│   │   └── server.py              # WebSocket telemetry sidecar
│   └── cli/
│       ├── main.py                # Typer CLI entrypoint
│       └── interactive.py         # Interactive REPL & slash commands
├── tests/
│   ├── test_full_pipeline.py      # Pipeline integration tests
│   ├── test_interactive_repl.py   # REPL & tool tests
│   └── test_v2_features.py        # 🆕 v2.0.0 feature tests
├── CHANGELOG.md                   # 🆕 Version history
├── pyproject.toml                 # Package configuration
└── README.md                      # This file
```

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
PYTHONPATH=. python -m pytest tests/ -v
```

---

## 🔌 Creating Plugins

Create a Python file in `~/.aether/plugins/`:

```python
# ~/.aether/plugins/my_scanner.py

PLUGIN_META = {
    "name": "my_scanner",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "Custom security scanner",
    "type": "scanner",
}

def register(manager):
    manager.register_tool("my_custom_tool", my_tool_handler)
    manager.register_command("myscan", my_scan_command)

def my_tool_handler(file_path: str) -> str:
    return f"Scanned {file_path}"

def my_scan_command():
    print("Running custom scan!")
```

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with 🛡️ by the Aether Security Team**

*Deterministic Defense. Probabilistic Intelligence. Autonomous Resilience.*

</div>
