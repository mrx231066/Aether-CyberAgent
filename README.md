<div align="center">

# 🛡️ AETHER-CYBERAGENT

### Autonomous Multi-Agent AI Security Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![SARIF](https://img.shields.io/badge/SARIF-v2.1.0-orange?style=for-the-badge)](https://sarifweb.azurewebsites.net/)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

**Deterministic Computer Science × Probabilistic AI**

*AST Parsing · Graph Theory · Formal Logic · Google Gemini · Self-Healing Loops*

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [Usage](#-usage) · [Dashboard](#-dashboard) · [Contributing](#-contributing)

---

</div>

## 🧬 What is Aether-CyberAgent?

**Aether-CyberAgent** is an elite, autonomous, multi-agent AI security platform that goes far beyond simple LLM wrappers. It fuses **deterministic computer science** — AST parsing, graph theory, and formal logic verification — with **probabilistic AI** powered by Google Gemini to create a **self-healing, autonomic software engine**.

It scans your Python codebase, detects vulnerabilities deterministically, generates AI-powered patches, mathematically verifies them, and outputs industry-standard SARIF reports — all in an autonomous loop that self-corrects on failure.

### ✨ Key Features

- 🔍 **Deterministic Vulnerability Detection** — Python AST-based scanning, not regex guessing
- 🧠 **AI-Powered Remediation** — Google Gemini generates type-annotated, secure code patches
- 📐 **Mathematical Verification** — Z3 SMT Solver proves correctness, Hypothesis fuzzes edge cases
- 🔄 **Self-Healing Loop** — Autonomous retry engine that learns from verification failures
- 🐳 **Sandboxed Execution** — Every test runs in isolated Docker containers
- 📊 **Live Dashboard** — Real-time Streamlit visualization of the security pipeline
- 📋 **SARIF v2.1.0 Reports** — Native GitHub Security tab integration
- 🗺️ **Blast Radius Analysis** — NetworkX graphs map vulnerability impact across your codebase

---

## 🏛️ Architecture

Aether-CyberAgent implements a **defensive Cybersecurity Team Spectrum** model. Each agent maps to a distinct security role — there are **no offensive components**. This is a pure defensive, self-correcting system.

### The Team Spectrum

```
┌──────────────────────────────────────────────────────────────────────┐
│                     🥇 GOLD TEAM (Orchestrator)                      │
│              Autonomic Self-Healing Loop · Max 3 Retries             │
│                                                                      │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐  │
│  │ 🔵 BLUE    │──▶│ 🟡 YELLOW  │──▶│ 🟣 PURPLE  │──▶│ 🟢 GREEN   │  │
│  │ AST Audit  │   │ AI Patch   │   │ Z3 Verify  │   │ Docker Run │  │
│  │ + GraphRAG │   │ + Gemini   │   │ + Hypothes │   │ + CI/CD    │  │
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
| 🔵 **Blue Team** | Static Auditor & GraphRAG Memory | Parses Python ASTs to find deterministic vulnerabilities (SQL injection, insecure deserialization, dangerous `eval`/`exec` calls). Uses NetworkX to map import dependencies and calculate blast radius. |
| 🟡 **Yellow Team** | Remediation & Refactoring | Integrates with Google Gemini API via `google-genai` SDK. Receives Blue Team findings and generates secure, type-annotated code patches using strict Pydantic structured outputs. |
| 🟣 **Purple Team** | Formal Verification | Verifies patches mathematically. Z3 SMT Solver checks variable bounds and logic constraints. Hypothesis generates property-based boundary tests to prevent regressions. |
| 🥇 **Gold Team** | Autonomic Self-Correction | The orchestrator. If Purple Team verification fails, Gold Team intercepts the failure trace, rolls back state, updates prompt context, and retries Yellow Team — up to 3 attempts. |
| 🟢 **Green Team** | DevSecOps Automation | Executes the pipeline in isolated Docker sandboxes. Manages GitHub Actions integration for CI/CD. |
| ⚪ **White Team** | Governance & Reporting | Formats verified patches into SARIF v2.1.0 JSON logs for native ingestion into GitHub Security tabs. |

---

## 🛠️ Tech Stack

Every component is **100% free and open source**.

| Component | Library | Purpose |
|-----------|---------|---------|
| 🤖 AI Engine | [`google-genai`](https://pypi.org/project/google-genai/) | Gemini 2.5 Flash (Free Tier) |
| 📦 Structured Output | [`pydantic`](https://docs.pydantic.dev/) | Type-safe AI response schemas |
| 💻 Terminal UI | [`rich`](https://rich.readthedocs.io/) + [`typer`](https://typer.tiangolo.com/) | Beautiful CLI tables, spinners, trees |
| 📊 Web Dashboard | [`streamlit`](https://streamlit.io/) | Real-time DAG visualization & diffs |
| 🗺️ Graph Memory | [`networkx`](https://networkx.org/) | Dependency blast-radius calculation |
| 📐 Formal Logic | [`z3-solver`](https://github.com/Z3Prover/z3) | SMT mathematical verification |
| 🧪 Property Testing | [`hypothesis`](https://hypothesis.readthedocs.io/) | Fuzzing & edge-case generation |
| 🐳 Sandbox | [`docker`](https://docker-py.readthedocs.io/) | Isolated test execution |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker** (running daemon)
- **Google Gemini API Key** ([Get one free](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/aether-cyberagent.git
cd aether-cyberagent

# Install with pip
pip install -e .

# Or with Poetry
poetry install
```

### Configuration

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Verify Docker is running
docker info
```

### GitHub Codespaces

This project includes a `.devcontainer` configuration for one-click setup in GitHub Codespaces with Python 3.11 and Docker-in-Docker support.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_USERNAME/aether-cyberagent)

---

## 💡 Usage

### Run a Security Scan

```bash
# Scan the current directory
aether scan .

# Scan a specific path
aether scan ./src/my_project

# Scan with verbose output
aether scan ./src --verbose
```

### Launch the Dashboard

```bash
# Start the Streamlit real-time dashboard
aether dashboard
```

### Verify a Specific File

```bash
# Run formal verification on a file
aether verify ./src/module.py
```

### Example Output

```
🛡️ Aether-CyberAgent v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵 Blue Team: Scanning 47 files...
   ├── Found 3 vulnerabilities
   ├── eval() call at auth.py:42
   ├── exec() call at utils.py:118
   └── subprocess.Popen(shell=True) at deploy.py:67

🗺️ Blast Radius Analysis:
   └── auth.py → 12 dependent modules affected

🟡 Yellow Team: Generating patches via Gemini 2.5 Flash...
   └── ✅ 3 patches generated (structured output)

🟣 Purple Team: Formal verification...
   ├── Z3 boundary check: ✅ PASS
   └── Hypothesis fuzzing: ✅ PASS (200 cases)

🟢 Green Team: Docker sandbox execution...
   └── ✅ All tests passed in isolated container

⚪ White Team: Generating SARIF report...
   └── 📋 Report saved: .aether/reports/sarif_2025-01-15.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Scan complete. 3 vulnerabilities patched & verified.
```

---

## 📊 Dashboard

The Streamlit dashboard provides real-time visibility into the security pipeline:

- **🗺️ DAG Visualization** — Interactive dependency graph showing vulnerability propagation
- **📝 Code Diffs** — Side-by-side before/after comparison of patched code
- **📈 Metrics** — Scan history, vulnerability trends, and verification success rates
- **🔄 Live Status** — Real-time progress of the autonomic self-healing loop

```bash
aether dashboard
# Opens at http://localhost:8501
```

---

## 📁 Project Structure

```
aether-cyberagent/
├── .devcontainer/
│   └── devcontainer.json              # GitHub Codespaces setup
├── .github/
│   └── workflows/
│       └── aether-security.yml        # CI/CD pipeline
├── aether/
│   ├── ai/
│   │   └── gemini_client.py           # 🟡 Gemini SDK + Pydantic schemas
│   ├── agents/
│   │   ├── blue_auditor.py            # 🔵 AST vulnerability detection
│   │   ├── purple_verifier.py         # 🟣 Z3 + Hypothesis verification
│   │   └── gold_autonomic.py          # 🥇 Self-healing orchestrator
│   ├── engine/
│   │   ├── graph_memory.py            # NetworkX dependency graphs
│   │   └── sandbox.py                 # 🟢 Docker sandboxed execution
│   ├── reports/
│   │   └── sarif.py                   # ⚪ SARIF v2.1.0 report generator
│   ├── dashboard/
│   │   └── app.py                     # Streamlit live dashboard
│   └── cli/
│       └── main.py                    # Typer CLI entry points
├── tests/
│   └── test_full_pipeline.py          # Integration test suite
├── pyproject.toml                     # Project configuration
├── ARCHITECTURE.md                    # Technical deep-dive
└── README.md                          # You are here
```

---

## 🔄 CI/CD Integration

Aether-CyberAgent includes a GitHub Actions workflow (`aether-security.yml`) that automatically runs on pull requests:

1. Scans all changed Python files
2. Runs the full autonomic pipeline
3. Uploads SARIF results to GitHub Security tab
4. Comments on the PR with findings

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

## ⚠️ Disclaimer

Aether-CyberAgent is a **defensive security tool**. It is designed to identify and remediate vulnerabilities in your own codebase. Always review AI-generated patches before deploying to production. The self-healing loop provides high confidence through formal verification, but human oversight remains essential.

---

<div align="center">

**Built with 🛡️ by the Aether Security Team**

*Deterministic Defense. Probabilistic Intelligence. Autonomous Resilience.*

</div>
