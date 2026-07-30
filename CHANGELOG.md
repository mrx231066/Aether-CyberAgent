# Changelog

All notable changes to Aether-CyberAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-30

### Added
- **🔴 Red Team Agent** (`red_attacker.py`) — Active attack surface enumeration:
  - Endpoint discovery from Flask/FastAPI/Django route decorators
  - Auth bypass detection on sensitive routes missing auth decorators
  - SQL injection pattern detection in query builders (f-strings, .format())
  - SSRF/IDOR pattern detection (user-controlled URLs in requests)
  - Entropy-based secret scanning (Shannon entropy > 4.5 on 32+ char strings)
  - Pattern-based secret detection (OpenAI keys, GitHub PATs, AWS keys, JWTs, Slack tokens)
  - Dangerous default detection (DEBUG=True, CORS *, SSL verify=False)
  - Attack surface scoring (0-10) with automated recommendations
- **📦 Plugin System** (`plugins.py`) — Hot-loadable plugin architecture:
  - Single-file and package plugins from `~/.aether/plugins/`
  - Runtime registration of custom tools, commands, and scanner hooks
  - Singleton PluginManager with discovery and lifecycle management
- **📄 HTML Report Generator** (`html_report.py`):
  - Standalone dark-themed HTML security reports via Jinja2
  - Full pipeline visualization: metrics, patches, attack vectors, event logs
  - Auto-generated alongside SARIF reports during scans
- **🔄 Watch Mode** (`watcher.py`):
  - `aether watch .` — continuous filesystem monitoring with watchdog
  - Debounced file change detection (configurable delay)
  - Auto-triggers Blue Team scanning on modified .py files
- **CLI Commands**:
  - `aether watch [path]` — Start watch mode
  - `aether redscan [path]` — Run Red Team enumeration
  - `aether plugins` — List and manage loaded plugins
  - `/redscan [path]` — REPL slash command for Red Team scan
  - `/plugins` — REPL slash command for plugin listing
- `py.typed` marker for PEP 561 typed package support
- Missing `__init__.py` files for `dashboard/` and `web/` packages
- PyPI classifiers, project URLs, and optional dependency groups
- Comprehensive test suite for all v2.0.0 features (`test_v2_features.py`)

### Fixed
- **Version string mismatch** — Unified all version references to `2.0.0`:
  - `__init__.py`, `pyproject.toml`, REPL banner, CLI banner, SARIF driver, Gold Team banner
- **Broken `select_model_interactively()`** — Was treating model list as strings when `get_available_models()` returns dicts
- **Missing `Config.OFFLINE_MODE`** — Referenced in `router.py` but never defined
- **Deprecated `datetime.utcnow()`** — Replaced with `datetime.now(timezone.utc)` in `blue_auditor.py`
- **Broken test assertions** — Fixed `test_get_available_models_*` tests to handle dict-based model format
- **Missing dependencies** — Added `watchdog`, `jinja2` to core deps; `fastapi`, `uvicorn`, `pandas` as optional

### Changed
- Bumped minimum Python version to `3.11+`
- Scan pipeline now includes Red Team enumeration and HTML report generation
- Updated all stale docstring version references
- Enhanced `Config` class with `OFFLINE_MODE`, `WATCH_MODE` attributes
- Enhanced `SessionState` with `verbose_tools` attribute
- Updated `pyproject.toml` with proper classifiers and optional dependency groups

## [1.1.0] - 2026-07-15

### Added
- Interactive Agent REPL (`aether` command)
- Google Gemini function calling with tool declarations
- Self-correction loop (Gold Team, up to 3 retries)
- Vision context loading for image files
- Session time-travel (`/rollback`, `/branch`, `/switch`)
- NL-to-Shell translation for OS commands
- Theme engine with 5 presets
- Token quota tracking
- Setup wizard (`aether --setup`)
- WebSocket telemetry sidecar
- Silver Guardian ethical boundary daemon
- GraphRAG with SQLite caching
- MCP client stubs
- ADB and GitHub connectors

## [1.0.0] - 2026-07-01

### Added
- Core multi-agent security pipeline (Blue → Yellow → Purple → Gold)
- Blue Team AST-based vulnerability scanner
- Yellow Team Gemini-powered code remediation
- Purple Team Z3 + Hypothesis formal verification
- Gold Team autonomic self-healing loop
- SARIF v2.1.0 report generation
- Streamlit dashboard
- NetworkX dependency graph with blast radius analysis
- Typer CLI with scan, verify, and dashboard commands
