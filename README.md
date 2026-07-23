<div align="center">

# 🛡️ AETHER-CYBERAGENT

### Autonomous Multi-Agent AI Security Platform & Terminal Co-Pilot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![SARIF](https://img.shields.io/badge/SARIF-v2.1.0-orange?style=for-the-badge)](https://sarifweb.azurewebsites.net/)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

**Deterministic Computer Science × Probabilistic AI**

*AST Parsing · Graph Theory · Formal Logic · Google Gemini · Self-Healing Loops · Interactive REPL*

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [Usage](#-usage) · [Dashboard](#-dashboard) · [Contributing](#-contributing)

---

</div>

## 🧬 What is Aether-CyberAgent?

**Aether-CyberAgent** is an elite, autonomous, multi-agent AI security platform and terminal co-pilot. It fuses **deterministic computer science** (AST parsing, graph theory, formal logic) with **probabilistic AI** (Google Gemini function calling) to create a **self-healing, autonomic software engine**.

Version 0.2.0 introduces the **Antigravity Interactive Agent REPL**, transforming Aether from a CLI scanner into a full autonomous software developer and security team co-pilot that can converse, write scripts, execute terminal commands, and self-correct when errors occur.

### ✨ Key Features (v0.2.0)

- 💬 **Interactive Agent REPL** — Converse with Aether dynamically in a rich terminal interface.
- 🛠️ **Autonomous Tool Execution** — Aether can read/write files and execute shell scripts safely.
- 🔄 **Self-Correction Loop** — If a script fails, the Gold Team intercepts the stderr and feeds it back to the Yellow Team for autonomous auto-fixing (up to 3 retries).
- 🔍 **Deterministic Vulnerability Detection** — Python AST-based scanning, not regex guessing.
- 🧠 **AI-Powered Remediation** — Google Gemini generates type-annotated, secure code patches.
- 📐 **Mathematical Verification** — Z3 SMT Solver proves correctness, Hypothesis fuzzes edge cases.
- 📊 **Live Dashboard** — Real-time Streamlit visualization of the security pipeline.
- 📋 **SARIF v2.1.0 Reports** — Native GitHub Security tab integration.

---

## 🏛️ Architecture

Aether-CyberAgent implements a **defensive Cybersecurity Team Spectrum** model. Each agent maps to a distinct security role — there are **no offensive components**. This is a pure defensive, self-correcting system.

### The Team Spectrum

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     🥇 GOLD TEAM (Orchestrator)                      │
│              Autonomic Self-Healing Loop · Max 3 Retries             │
│                                                                      │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐  │
│  │ 🔵 BLUE    │──▶│ 🟡 YELLOW  │──▶│ 🟣 PURPLE  │──▶│ 🟢 GREEN   │  │
│  │ AST Audit  │   │ AI Patch   │   │ Z3 Verify  │   │ Tool Run   │  │
│  │ + GraphRAG │   │ + Scripts  │   │ + Hypothes │   │ + Sandbox  │  │
│  └────────────┘   └─────▲──────┘   └─────┬──────┘   └─────┬──────┘  │
│                         │                 │                 │         │
│                         │    ❌ FAIL      │                 │         │
│                         └─────────────────┘                 │         │
│                                                             ▼         │
│                                                     ┌────────────┐   │
│                                                     │ ⚪ WHITE   │   │
│                                                     │ SARIF v2.1 │   │
│                                                     │ + Reports  │   │
│                                                     └────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

| Team | Role | Mechanism |
|:----:|------|-----------|
| 🔵 **Blue Team** | Static Auditor | Parses Python ASTs to find deterministic vulnerabilities (SQL injection, insecure deserialization, dangerous `eval`/`exec`). Calculates blast radius via NetworkX. |
| 🟡 **Yellow Team** | Autonomous Developer | Integrates with Google Gemini via function calling. Generates scripts, patches code, and invokes read/write/shell tools autonomously. |
| 🟣 **Purple Team** | Formal Verification | Verifies patches mathematically. Z3 SMT Solver checks variable bounds and logic constraints. Hypothesis generates property-based boundary tests. |
| 🥇 **Gold Team** | Autonomic Orchestrator | If Purple Team verification or Green Team script execution fails, Gold Team intercepts the failure trace, updates context, and retries Yellow Team. |
| 🟢 **Green Team** | Tool Execution Engine | Executes scripts and shell commands in isolated sandboxes with strict timeouts. |
| ⚪ **White Team** | Governance & Reporting | Formats verified patches into SARIF v2.1.0 JSON logs for CI/CD ingestion. |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker** (running daemon, for sandbox execution)
- **Google Gemini API Key** ([Get one free](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/mrx231066/Aether-CyberAgent.git
cd Aether-CyberAgent

# Install the CLI package
pip install -e .
```

---

## 💡 Usage

### Launch Interactive Agent REPL (New in v0.2.0)

Simply type `aether` to launch the Antigravity Interactive Agent REPL. It will dynamically discover available Gemini models and prompt for your API key if not configured.

```bash
aether
```

**Supported Slash Commands:**
- `/help` — Displays interactive command matrix & agent team status.
- `/scan [path]` — Executes full background multi-agent security scan.
- `/model` — Opens interactive model switcher menu.
- `/auth` — Updates stored API key/config.
- `/status` — Displays dependency graph metrics & memory state.
- `/run <script>` — Safely runs a script in the execution sandbox.
- `/clear` — Clears terminal output.
- `/exit` or `/quit` — Closes REPL session.

**Autonomous Script Execution & Self-Correction:**
If you ask Aether to write a script in the chat, it will generate it, write it to disk, and execute it. If it fails, the **Gold Team** intercepts the traceback and auto-fixes the code up to 3 times!

### Run a Standalone Security Scan

```bash
# Scan the current directory
aether scan .

# Scan a specific path
aether scan ./src/my_project
```

### Launch the Visual Dashboard

```bash
# Start the Streamlit real-time dashboard
aether dashboard
```

### Verify a Specific File

```bash
# Run formal verification on a specific file patch
aether verify ./src/module.py
```

---

## 📁 Project Structure (v0.2.0)

```text
aether-cyberagent/
├── aether/
│   ├── ai/
│   │   └── gemini_client.py       # Dynamic model discovery & Structured Output
│   ├── agents/
│   │   ├── blue_auditor.py        # Static AST parser
│   │   ├── yellow_patcher.py      # Refactoring & script generator agent
│   │   ├── purple_verifier.py     # Z3 formal logic & property testing
│   │   └── gold_autonomic.py      # Self-correction execution loop
│   ├── engine/
│   │   ├── graph_memory.py        # NetworkX repository dependency graph
│   │   ├── sandbox.py             # Docker runner
│   │   └── tools.py               # Autonomous tool execution engine (read/write/shell)
│   ├── reports/
│   │   └── sarif.py               # White team SARIF v2.1.0 exporter
│   ├── dashboard/
│   │   └── app.py                 # Streamlit visualizer
│   └── cli/
│       ├── main.py                # Typer CLI entrypoint
│       └── interactive.py         # Antigravity Interactive REPL & Slash Commands
├── tests/
│   ├── test_full_pipeline.py      # Scan pipeline tests
│   └── test_interactive_repl.py   # REPL & tool engine tests
├── pyproject.toml                 # Package configuration
└── README.md                      # Documentation
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
