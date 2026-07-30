"""Theme Engine for Aether-CyberAgent v4.0.1"""
import json
from pathlib import Path
from rich.console import Console

console = Console()
THEME_FILE = Path.home() / ".aether" / "theme.json"

THEME_PRESETS = {
    "Tokyo Night": {"primary": "#7aa2f7", "secondary": "#bb9af7", "bg": "#1a1b26"},
    "Dracula Cyber": {"primary": "#ff79c6", "secondary": "#8be9fd", "bg": "#282a36"},
    "Matrix Code": {"primary": "#00ff00", "secondary": "#008800", "bg": "#000000"},
    "Cyberpunk 2077": {"primary": "#fede00", "secondary": "#00f0ff", "bg": "#120ef6"},
    "Nord Minimal": {"primary": "#88c0d0", "secondary": "#81a1c1", "bg": "#2e3440"},
}

class ThemeEngine:
    @staticmethod
    def get_current_theme():
        if THEME_FILE.exists():
            try:
                return json.loads(THEME_FILE.read_text())
            except Exception:
                pass
        return THEME_PRESETS["Tokyo Night"]

    @staticmethod
    def set_theme(theme_name: str):
        if theme_name in THEME_PRESETS:
            THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
            THEME_FILE.write_text(json.dumps(THEME_PRESETS[theme_name]))
            console.print(f"[{THEME_PRESETS[theme_name]['primary']}]🎨 Theme changed to {theme_name}[/]")
            return True
        console.print(f"[red]❌ Theme {theme_name} not found. Available: {', '.join(THEME_PRESETS.keys())}[/red]")
        return False
