"""Plugin System for Aether-CyberAgent v4.0.1.

Hot-loadable plugin architecture supporting:
- Python plugins from ~/.aether/plugins/
- Declarative YAML plugin manifests
- Runtime registration of custom tools, agents, and commands
"""

import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

PLUGIN_DIR = Path.home() / ".aether" / "plugins"


@dataclass
class PluginMetadata:
    """Metadata describing a loaded plugin."""
    name: str
    version: str = "0.1.0"
    author: str = "Unknown"
    description: str = ""
    plugin_type: str = "generic"  # 'tool', 'agent', 'command', 'scanner', 'generic'
    entry_point: str = ""
    enabled: bool = True


@dataclass
class PluginInstance:
    """A loaded and initialized plugin."""
    metadata: PluginMetadata
    module: Any = None
    hooks: Dict[str, Callable] = field(default_factory=dict)


class PluginManager:
    """Manages the lifecycle of Aether plugins.

    Plugin Structure:
        ~/.aether/plugins/
        ├── my_plugin/
        │   ├── __init__.py       # Must export: PLUGIN_META (dict) and register(manager)
        │   └── ...
        └── simple_plugin.py      # Single-file plugin with PLUGIN_META and register()
    """

    _instance: Optional["PluginManager"] = None
    _plugins: Dict[str, PluginInstance] = {}
    _tool_hooks: Dict[str, Callable] = {}
    _command_hooks: Dict[str, Callable] = {}
    _scanner_hooks: List[Callable] = []

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def discover_and_load(self) -> List[PluginMetadata]:
        """Discover and load all plugins from the plugin directory."""
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        loaded: List[PluginMetadata] = []

        # Single-file plugins (*.py)
        for py_file in PLUGIN_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            meta = self._load_single_file_plugin(py_file)
            if meta:
                loaded.append(meta)

        # Package plugins (directories with __init__.py)
        for pkg_dir in PLUGIN_DIR.iterdir():
            if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
                if pkg_dir.name.startswith("_"):
                    continue
                meta = self._load_package_plugin(pkg_dir)
                if meta:
                    loaded.append(meta)

        if loaded:
            console.print(f"[bold green]🔌 Loaded {len(loaded)} plugin(s)[/bold green]")
        return loaded

    def _load_single_file_plugin(self, path: Path) -> Optional[PluginMetadata]:
        """Load a single-file Python plugin."""
        try:
            spec = importlib.util.spec_from_file_location(path.stem, str(path))
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"aether_plugin_{path.stem}"] = module
            spec.loader.exec_module(module)

            meta_dict = getattr(module, "PLUGIN_META", {})
            metadata = PluginMetadata(
                name=meta_dict.get("name", path.stem),
                version=meta_dict.get("version", "0.1.0"),
                author=meta_dict.get("author", "Unknown"),
                description=meta_dict.get("description", ""),
                plugin_type=meta_dict.get("type", "generic"),
            )

            instance = PluginInstance(metadata=metadata, module=module)

            # Call register() if it exists
            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                register_fn(self)

            self._plugins[metadata.name] = instance
            console.print(f"  [dim]📦 {metadata.name} v{metadata.version} ({metadata.plugin_type})[/dim]")
            return metadata

        except Exception as e:
            console.print(f"[red]  ❌ Failed to load plugin {path.name}: {e}[/red]")
            return None

    def _load_package_plugin(self, pkg_dir: Path) -> Optional[PluginMetadata]:
        """Load a package-style plugin."""
        try:
            init_path = pkg_dir / "__init__.py"
            spec = importlib.util.spec_from_file_location(
                f"aether_plugin_{pkg_dir.name}", str(init_path),
                submodule_search_locations=[str(pkg_dir)]
            )
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"aether_plugin_{pkg_dir.name}"] = module
            spec.loader.exec_module(module)

            meta_dict = getattr(module, "PLUGIN_META", {})
            metadata = PluginMetadata(
                name=meta_dict.get("name", pkg_dir.name),
                version=meta_dict.get("version", "0.1.0"),
                author=meta_dict.get("author", "Unknown"),
                description=meta_dict.get("description", ""),
                plugin_type=meta_dict.get("type", "generic"),
            )

            instance = PluginInstance(metadata=metadata, module=module)

            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                register_fn(self)

            self._plugins[metadata.name] = instance
            console.print(f"  [dim]📦 {metadata.name} v{metadata.version} ({metadata.plugin_type})[/dim]")
            return metadata

        except Exception as e:
            console.print(f"[red]  ❌ Failed to load plugin {pkg_dir.name}: {e}[/red]")
            return None

    def register_tool(self, name: str, handler: Callable) -> None:
        """Register a custom tool that the agent can invoke."""
        self._tool_hooks[name] = handler
        console.print(f"  [dim]🔧 Tool registered: {name}[/dim]")

    def register_command(self, name: str, handler: Callable) -> None:
        """Register a custom slash command."""
        self._command_hooks[name] = handler
        console.print(f"  [dim]⚡ Command registered: /{name}[/dim]")

    def register_scanner(self, scanner_fn: Callable) -> None:
        """Register a custom scanner that runs during security audits."""
        self._scanner_hooks.append(scanner_fn)
        console.print(f"  [dim]🔍 Scanner registered[/dim]")

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a registered tool handler."""
        return self._tool_hooks.get(name)

    def get_command(self, name: str) -> Optional[Callable]:
        """Get a registered command handler."""
        return self._command_hooks.get(name)

    def get_scanners(self) -> List[Callable]:
        """Get all registered scanner hooks."""
        return list(self._scanner_hooks)

    def list_plugins(self) -> None:
        """Display all loaded plugins."""
        if not self._plugins:
            console.print("[yellow]No plugins loaded. Add plugins to ~/.aether/plugins/[/yellow]")
            return

        table = Table(title="🔌 Loaded Plugins", box=box.ROUNDED, border_style="cyan")
        table.add_column("Name", style="bold white")
        table.add_column("Version", style="yellow")
        table.add_column("Type", style="cyan")
        table.add_column("Author", style="green")
        table.add_column("Description", style="dim")

        for name, inst in self._plugins.items():
            m = inst.metadata
            table.add_row(m.name, m.version, m.plugin_type, m.author, m.description)

        console.print(table)

    def get_loaded_plugins(self) -> Dict[str, PluginInstance]:
        """Return all loaded plugin instances."""
        return dict(self._plugins)
