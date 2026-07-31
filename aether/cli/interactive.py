"""Aether-CyberAgent Interactive REPL & Slash Commands.

Provides an interactive terminal session where the agent acts as a
full software developer and security team co-pilot.
Powered by Rich for rendering and prompt_toolkit for input history.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()

from aether.auth import load_config, save_config
from aether.ai.provider_manager import ProviderManager

REPL_BANNER = """[bold cyan]
    █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗        [bold white]v4.0.1[/bold white]
   ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗
   ███████║█████╗     ██║   ███████║█████╗  ██████╔╝
   ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗
   ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║
   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
[/bold cyan]
[bold cyan]Developed by Jashan Nain[/bold cyan]
"""

# ── Configuration Helpers ──

def _select_model(api_key: str) -> str:
    """Interactive model selection using dynamic discovery."""
    from aether.ai.gemini_client import GeminiClient

    console.print("[bold cyan]🔍 Discovering available Gemini models...[/bold cyan]")
    with console.status("[bold green]Agent working...[/bold green]", spinner="circle"):
        models = GeminiClient.get_available_models(api_key=api_key)

    if not sys.stdin.isatty():
        return models[0]["name"] if models else GeminiClient.DEFAULT_MODEL

    table = Table(title="🤖 Available Models", box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="bold yellow", justify="right")
    table.add_column("Model", style="bold white")
    table.add_column("Info", style="green")

    for idx, m_dict in enumerate(models, 1):
        name = m_dict.get("name", "")
        info = m_dict.get("info", "")
        table.add_row(str(idx), name, info)

    console.print(table)
    choices = [str(i) for i in range(1, len(models) + 1)]
    choice = Prompt.ask(
        "[bold yellow]Select model[/bold yellow]", choices=choices, default="1"
    )
    selected = models[int(choice) - 1]["name"]
    console.print(f"[green]✅ Default model set to: {selected}[/green]\n")
    return selected


# ── Slash Command Router ──

def handle_slash_command(command: str, api_key: str, model: str) -> Optional[str]:
    """Route and execute slash commands."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        console.print("\n[bold cyan]👋 Shutting down Aether REPL. Stay secure.[/bold cyan]")
        return "EXIT"

    elif cmd == "/help":
        _show_help()

    elif cmd == "/scan":
        _run_scan(args or ".", api_key, model)

    elif cmd == "/model":
        new_model = _select_model(api_key)
        save_config({"model": new_model})
        return new_model

    elif cmd == "/auth":
        new_key = Prompt.ask(
            "[bold cyan]Enter new Gemini API Key[/bold cyan]", password=True
        )
        if new_key:
            os.environ["GEMINI_API_KEY"] = new_key
            save_config({"api_key": new_key})
            console.print("[green]✅ API Key updated.[/green]")

    elif cmd == "/status":
        _show_status(model)

    elif cmd == "/quota":
        _show_quota()

    elif cmd == "/run":
        if args:
            _run_script(args)
        else:
            console.print("[yellow]Usage: /run <script_path>[/yellow]")

    elif cmd == "/rollback":
        from aether.cli.session_manager import SessionManager
        n = int(args) if args.isdigit() else 1
        SessionManager.rollback(n)
        
    elif cmd == "/branch":
        from aether.cli.session_manager import SessionManager
        if args:
            SessionManager.branch(args)
        else:
            console.print("[yellow]Usage: /branch <branch_name>[/yellow]")
            
    elif cmd == "/switch":
        from aether.cli.session_manager import SessionManager
        if args:
            SessionManager.switch_branch(args)
        else:
            console.print("[yellow]Usage: /switch <branch_name>[/yellow]")
            
    elif cmd == "/mcp":
        from aether.engine.mcp_client import MCPClient
        if args == "list":
            MCPClient.list_servers()
        elif args.startswith("connect "):
            url = args.split(" ", 1)[1]
            MCPClient.connect(url)
        else:
            console.print("[yellow]Usage: /mcp list | /mcp connect <url>[/yellow]")
            
    elif cmd == "/skills":
        from aether.engine.skills import SkillsLoader
        skills = SkillsLoader.discover_skills()
        if skills:
            console.print("[bold cyan]🛠️  Local Skills Loaded:[/bold cyan]")
            for s in skills:
                console.print(f" - {s}")
        else:
            console.print("[yellow]No local skills found in ~/.aether/skills/[/yellow]")

    elif cmd == "/clear":
        os.system("clear" if os.name != "nt" else "cls")

    elif cmd == "/logout":
        from aether.config import SessionState
        from aether.cli.main import CONFIG_PATH
        if Confirm.ask("[bold red]Are you sure you want to logout? This will clear all credentials and configuration.[/bold red]"):
            if CONFIG_PATH.exists():
                CONFIG_PATH.unlink()
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            SessionState.chat_history.clear()
            console.print("[green]✅ Successfully logged out.[/green]")
            return "EXIT"

    elif cmd == "/theme":
        from aether.cli.theme_engine import ThemeEngine
        if args:
            ThemeEngine.set_theme(args)
        else:
            console.print("[yellow]Usage: /theme <theme_name>[/yellow]")

    elif cmd == "/redscan":
        _run_redscan(args or ".")

    elif cmd == "/plugins":
        from aether.engine.plugins import PluginManager
        manager = PluginManager()
        manager.discover_and_load()
        manager.list_plugins()

    elif cmd == "/yolo":
        from aether.config import SessionState
        if args == "off":
            SessionState.yolo_mode = False
            console.print("🛡️ [bold blue]YOLO MODE DISABLED[/bold blue]\nNormal approval workflow restored.")
        else:
            SessionState.yolo_mode = True
            console.print("⚡ [bold yellow]YOLO MODE ENABLED[/bold yellow]\nRoutine authorized actions will execute automatically. High-risk and restricted operations remain protected by policy.")

    elif cmd == "/update":
        from aether.engine.self_update import SelfUpdateEngine
        if args == "check":
            SelfUpdateEngine.check_for_update(auto_check=True)
        elif args == "apply":
            SelfUpdateEngine.apply_update()
        else:
            console.print("[yellow]Usage: /update check | /update apply[/yellow]")

    elif cmd == "/provider":
        from aether.ai.provider_manager import ProviderManager
        from aether.ai.providers.google_gemini import GoogleGeminiAdapter
        
        # Auto-register default provider
        if "google_gemini" not in ProviderManager._providers:
            ProviderManager.register(GoogleGeminiAdapter())
        
        if not args:
            ProviderManager.status()
        elif args == "add":
            console.print("\n╭──────────────────────────────────────╮")
            console.print("│       [bold cyan]ADD AI PROVIDER[/bold cyan]                │")
            console.print("├──────────────────────────────────────┤")
            console.print("│ 1. OpenAI                            │")
            console.print("│ 2. Anthropic Claude                  │")
            console.print("│ 3. Google Gemini                     │")
            console.print("│ 4. Moonshot AI / Kimi                │")
            console.print("│ 5. Z.ai / GLM                        │")
            console.print("│ 6. OpenRouter                        │")
            console.print("│ 7. Import Custom Provider            │")
            console.print("╰──────────────────────────────────────╯")
            
            choice = Prompt.ask("Select provider", choices=[str(i) for i in range(1, 8)])
            if choice == "3":
                provider = GoogleGeminiAdapter()
                ProviderManager.register(provider)
                if provider.authenticate():
                    ProviderManager.switch_provider("google_gemini")
                    ProviderManager.refresh_models("google_gemini")
            else:
                console.print(f"[dim]Provider {choice} adapter initialized...[/dim]")
        elif args == "list":
            console.print("\n[bold cyan]🔌 Configured Providers:[/bold cyan]")
            for p_name, p_obj in ProviderManager._providers.items():
                active = "*" if p_name == ProviderManager._active_provider_name else " "
                console.print(f" {active} {p_obj.display_name} ({p_name})")
        elif args.startswith("remove "):
            p_name = args.split(" ", 1)[1]
            if p_name in ProviderManager._providers:
                ProviderManager._providers[p_name].disconnect()
                del ProviderManager._providers[p_name]
                if ProviderManager._active_provider_name == p_name:
                    ProviderManager._active_provider_name = None
                    ProviderManager._active_model_id = None
                console.print(f"[green]✅ Provider {p_name} removed.[/green]")
            else:
                console.print(f"[red]❌ Provider {p_name} not found.[/red]")
        elif args.startswith("use "):
            p_name = args.split(" ", 1)[1]
            try:
                ProviderManager.switch_provider(p_name)
                console.print(f"[green]✅ Switched to provider {p_name}[/green]")
            except Exception as e:
                console.print(f"[red]❌ {e}[/red]")
        elif args.startswith("test "):
            p_name = args.split(" ", 1)[1]
            provider = ProviderManager._providers.get(p_name)
            if provider:
                console.print(f"[dim]Testing connection to {provider.display_name}...[/dim]")
                if provider.health_check():
                    console.print(f"[green]✅ Connection to {provider.display_name} successful.[/green]")
                else:
                    console.print(f"[red]❌ Connection to {provider.display_name} failed.[/red]")
            else:
                console.print(f"[red]❌ Provider {p_name} not found.[/red]")
        elif args.startswith("models "):
            p_name = args.split(" ", 1)[1]
            models = ProviderManager._model_registry.get(p_name, [])
            if models:
                console.print(f"\n[bold cyan]📦 Models for {p_name}:[/bold cyan]")
                for m in models:
                    console.print(f" - {m.display_name} ({m.model_id})")
            else:
                console.print(f"[yellow]No models found for {p_name}. Try /provider refresh {p_name}[/yellow]")
        elif args.startswith("refresh "):
            p_name = args.split(" ", 1)[1]
            try:
                ProviderManager.refresh_models(p_name)
            except Exception as e:
                console.print(f"[red]❌ Refresh failed: {e}[/red]")
        else:
            console.print("[yellow]Invalid /provider command. Try add, list, remove, use, test, models, refresh.[/yellow]")

    elif cmd == "/model":
        from aether.ai.provider_manager import ProviderManager
        provider = ProviderManager.get_active_provider()
        
        if not provider:
            console.print("[bold red]❌ No active provider. Use /provider add first.[/bold red]")
            return
            
        if args == "refresh":
            ProviderManager.refresh_models(provider.name)
            return

        models = ProviderManager._model_registry.get(provider.name, [])
        if not models:
            console.print("[bold red]❌ No models discovered. Run /model refresh.[/bold red]")
            return
            
        console.print("\n╭─────────────────────────────────────────────╮")
        console.print(f"│        [bold cyan]AVAILABLE {provider.display_name.upper()} MODELS[/bold cyan]              │")
        console.print("├─────────────────────────────────────────────┤")
        
        for i, m in enumerate(models, 1):
            active_marker = "*" if m.model_id == ProviderManager._active_model_id else " "
            console.print(f"│ {i}. {active_marker} {m.display_name:<33} │")
            
        console.print("│                                             │")
        console.print("│ R. Refresh Models                           │")
        console.print("│ C. Continue                                 │")
        console.print("╰─────────────────────────────────────────────╯")
        
        choice = Prompt.ask("Select model", choices=[str(i) for i in range(1, len(models)+1)] + ["R", "r", "C", "c"])
        if choice.upper() == "R":
            ProviderManager.refresh_models(provider.name)
        elif choice.upper() != "C":
            idx = int(choice) - 1
            ProviderManager.set_active_model(models[idx].model_id)
            console.print(f"[bold green]✓ Active model set to: {models[idx].display_name}[/bold green]")

    elif cmd == "/tasks":
        from aether.engine.tasks import TaskEngine
        TaskEngine.list_tasks()

    else:
        console.print(
            f"[yellow]Unknown command: {cmd}. Type /help for available commands.[/yellow]"
        )

    return None


# ── Slash Command Implementations ──


def _show_help():
    """Display the command reference table."""
    table = Table(
        title="🛡️ Aether Interactive Commands",
        box=box.ROUNDED,
        border_style="cyan",
    )
    table.add_column("Command", style="bold yellow", min_width=18)
    table.add_column("Description", style="white")
    table.add_column("Team", style="bold cyan")

    table.add_row("/help", "Show this command reference", "—")
    table.add_row("/scan [path]", "Run full multi-agent security scan", "🔵🟡🟣🥇")
    table.add_row("/model", "Switch Gemini model interactively", "🟡 Yellow")
    table.add_row("/auth", "Update API key & credentials", "—")
    table.add_row("/status", "Show session state & graph metrics", "⚪ White")
    table.add_row("/quota", "Show token usage & estimated cost", "⚪ White")
    table.add_row("/run <script>", "Execute script in sandbox", "🟢 Green")
    table.add_row("/redscan [path]", "Run Red Team attack surface scan", "🔴 Red")
    table.add_row("/plugins", "List loaded plugins", "🔌")
    table.add_row("/clear", "Clear terminal output", "—")
    table.add_row("/theme <name>", "Switch UI color theme", "—")
    table.add_row("/logout", "Logout and clear credentials", "—")
    table.add_row("/exit", "Close REPL session", "—")
    table.add_row("", "", "")
    table.add_row("[dim]<any text>[/dim]", "[dim]Chat with Aether AI agent[/dim]", "[dim]🟡 Yellow[/dim]")

    console.print(table)


def _show_quota():
    """Display the Token Quota Engine panel."""
    from aether.config import SessionState
    
    tokens = SessionState.total_tokens
    cost_per_million = 0.075  # blended average for flash
    estimated_cost = (tokens / 1_000_000) * cost_per_million

    table = Table(title="💰 Quota Engine", box=box.ROUNDED, border_style="green")
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="bold yellow", justify="right")
    
    table.add_row("Session Total Tokens", f"{tokens:,}")
    table.add_row("Estimated Cost ($)", f"${estimated_cost:.5f}")
    
    console.print(table)


def _run_scan(path: str, api_key: str, model: str):
    """Execute a full multi-agent security scan."""
    from aether.agents.gold_autonomic import AutonomicEngine
    from aether.reports.sarif import SarifReporter

    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[bold red]❌ Path not found: {path}[/bold red]")
        return

    try:
        console.print(f"[bold cyan]🔵 Starting multi-agent scan on: {target}[/bold cyan]")
        engine = AutonomicEngine(max_retries=3, api_key=api_key, model=model)
        
        with console.status("[bold green]Agent working...[/bold green]", spinner="circle"):
            result = engine.execute_scan(str(target))

        if result.vulnerabilities_found > 0:
            reporter = SarifReporter()
            sarif_path = reporter.export_from_pipeline(result, ".aether/reports")
            console.print(f"[bold white]📋 SARIF report: {sarif_path}[/bold white]")

        if result.success:
            console.print("[bold green]✅ Scan complete — all clear.[/bold green]")
        else:
            console.print(
                f"[bold yellow]⚠️  {len(result.failed_patches)} patches failed verification.[/bold yellow]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Scan error: {e}[/bold red]")


def _run_redscan(path: str):
    """Execute Red Team attack surface enumeration."""
    from aether.agents.red_attacker import RedTeamAttacker

    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[bold red]❌ Path not found: {path}[/bold red]")
        return

    try:
        console.print(f"[bold red]🔴 Red Team: Enumerating attack surface on: {target}[/bold red]")
        attacker = RedTeamAttacker()
        with console.status("[bold green]Agent working...[/bold green]", spinner="circle"):
            report = attacker.enumerate_attack_surface(str(target))

        if report.vectors:
            console.print(f"[bold red]⚠️  {len(report.vectors)} attack vector(s) found.[/bold red]")
        else:
            console.print("[bold green]✅ No attack vectors found.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Red Team error: {e}[/bold red]")

def _show_status(model: str):
    """Display current session status and dependency graph metrics."""
    from aether.engine.graph_memory import CodeGraphMemory

    config = load_config()

    table = Table(
        title="📊 Aether Session Status", box=box.ROUNDED, border_style="cyan"
    )
    table.add_column("Property", style="bold yellow")
    table.add_column("Value", style="white")

    table.add_row("Active Model", model)
    table.add_row("Working Directory", str(Path.cwd()))
    table.add_row("Config File", str(CONFIG_PATH))
    table.add_row(
        "API Key", "✅ Configured" if config.get("api_key") else "❌ Missing"
    )

    try:
        graph = CodeGraphMemory()
        graph.build_from_directory(str(Path.cwd()))
        nodes = graph.get_file_nodes()
        table.add_row("Dependency Graph Nodes", str(len(nodes)))
    except Exception:
        table.add_row("Dependency Graph", "[dim]Not built[/dim]")

    console.print(table)


def _run_script(script_path: str):
    """Execute a script in the sandbox via the ToolEngine."""
    from aether.engine.tools import ToolEngine

    tools = ToolEngine()
    target = Path(script_path).resolve()

    if not target.exists():
        console.print(f"[bold red]❌ Script not found: {script_path}[/bold red]")
        return

    console.print(f"[bold green]🟢 Executing: {target.name}...[/bold green]")
    with console.status("[bold green]Agent working...[/bold green]", spinner="circle"):
        result = tools.execute_shell(f"python {target}", timeout=60)

    if result["stdout"]:
        console.print(
            Panel(result["stdout"].strip(), title="stdout", border_style="green")
        )
    if result["stderr"]:
        console.print(
            Panel(result["stderr"].strip(), title="stderr", border_style="red")
        )

    exit_code = result["exit_code"]
    if exit_code == 0:
        console.print("[green]✅ Script executed successfully.[/green]")
    elif result["timed_out"]:
        console.print("[yellow]⏱️  Script timed out.[/yellow]")
    else:
        console.print(f"[red]❌ Script failed with exit code {exit_code}.[/red]")


# ── Agent Chat Handler ──


def _chat_with_agent(user_input: str, api_key: str, model: str, patcher=None):
    """Route conversational queries to the Yellow Patcher agent."""
    from aether.agents.yellow_patcher import YellowPatcher

    try:
        if patcher is None:
            patcher = YellowPatcher(api_key=api_key, model=model)
        patcher.chat(user_input)
    except Exception as e:
        console.print(f"[bold red]❌ Agent error: {e}[/bold red]")

    return patcher


# ── Status Bar ──


def _render_status_bar(model: str) -> str:
    """Generate the REPL status bar text."""
    cwd = Path.cwd().name or "/"
    return f"[dim][ Model: {model} | Dir: {cwd} | Status: Ready ][/dim]"


# ── Main REPL Entry Point ──


def start_interactive_session():
    """Launch the Aether Interactive REPL session."""
    import os
    os.system("clear" if os.name != "nt" else "cls")
    
    try:
        from aether.agents.silver_guardian import SilverGuardian
        daemon = SilverGuardian()
        daemon.start()
    except Exception as e:
        console.print(f"[dim red]Warning: Could not start SilverGuardian daemon: {e}[/dim red]")

    console.print(REPL_BANNER)

    # Step 1: Check ProviderManager for authentication
    active_provider = ProviderManager.get_active_provider()
    model = ProviderManager._active_model_id if active_provider else "None (Use /provider add)"
    api_key = ""  # Legacy variable required by handlers

    if not active_provider:
        console.print("[dim yellow]No AI Provider configured. You are in offline mode. Type /provider add to set one up.[/dim yellow]\n")

    console.print(
        Panel(
            f"[bold white]Provider:[/bold white] {active_provider.display_name if active_provider else 'Not Configured'}\n"
            f"[bold white]Model:[/bold white] {model}\n"
            f"[bold white]Directory:[/bold white] {Path.cwd()}\n"
            f"[bold white]Commands:[/bold white] Type [bold yellow]/help[/bold yellow] or [bold yellow]/provider[/bold yellow] for setup",
            title="🚀 Session Active",
            border_style="green",
            box=box.ROUNDED,
        )
    )

    # Setup prompt_toolkit
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.key_binding import KeyBindings
    from aether.cli.ui_header import TopHeader, toggle_mode

    commands = ["/help", "/quota", "/diff", "/rollback", "/branch", "/mcp", "/skills", "/scan", "/model", "/auth", "/status", "/run", "/clear", "/exit", "/logout", "/theme", "/redscan", "/plugins"]
    completer = WordCompleter(commands, ignore_case=True)
    
    bindings = KeyBindings()
    
    @bindings.add("s-tab")
    def _(event):
        toggle_mode()
        event.app.invalidate()

    @bindings.add("c-o")
    def _(event):
        from aether.config import SessionState
        SessionState.verbose_tools = getattr(SessionState, "verbose_tools", False)
        SessionState.verbose_tools = not SessionState.verbose_tools
        event.app.invalidate()

    @bindings.add("?")
    def _(event):
        if not event.app.current_buffer.text:
            console.print("\n[bold cyan]⌨️  Aether Shortcuts[/bold cyan]")
            console.print("  [bold yellow]Shift+Tab[/bold yellow] : Toggle accept-edits / ask-before-edit")
            console.print("  [bold yellow]Ctrl+O[/bold yellow]    : Toggle verbose tool logs")
            console.print("  [bold yellow]Ctrl+C[/bold yellow]    : Cancel current input")
            event.app.current_buffer.reset()
        else:
            event.app.current_buffer.insert_text("?")
        
    @bindings.add("c-c")
    def _(event):
        # Graceful SIGINT
        console.print("\n[yellow]Keyboard interrupt detected. Type /exit to quit.[/yellow]")
        event.app.current_buffer.reset()

    header = TopHeader(model=model)
    session = PromptSession(
        completer=completer,
        key_bindings=bindings,
        bottom_toolbar=header.get_header_text,
        rprompt=header.get_rprompt_text,
    )

    patcher = None
    try:
        while True:
            # We use bottom_toolbar as the top status header for prompt_toolkit by putting it at the prompt line
            try:
                user_input = session.prompt("aether > ")
            except EOFError:
                console.print("\n[bold cyan]👋 Session ended.[/bold cyan]")
                break
            except KeyboardInterrupt:
                continue

            if not user_input.strip():
                continue

            # Phase 3: NL-to-Shell Translation
            from aether.engine.shell_translator import translate_nl_to_shell
            translated = translate_nl_to_shell(user_input.strip())
            if translated:
                user_input = translated

            if user_input.strip().startswith("/"):
                result = handle_slash_command(user_input.strip(), api_key, model)
                if result == "EXIT":
                    break
                elif result is not None:
                    model = result
                    header.model = model
                    patcher = None
            else:
                patcher = _chat_with_agent(
                    user_input.strip(), api_key, model, patcher
                )
                from aether.cli.session_manager import SessionManager
                SessionManager.prune_context()

    except Exception as e:
        console.print(f"\n[bold red]❌ REPL error: {e}[/bold red]")
