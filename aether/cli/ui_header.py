"""Bottom Status Toolbar (Command Bar) for Aether-CyberAgent."""

from aether.config import Config

class TopHeader:
    def __init__(self, model="Gemini 2.5 Pro"):
        self.model = model
        
    def get_header_text(self):
        from prompt_toolkit.formatted_text import HTML
        from aether.cli.theme_engine import ThemeEngine
        theme = ThemeEngine.get_current_theme()
        
        bg = theme.get("primary", "#7aa2f7")
        fg = theme.get("bg", "#1a1b26")
        
        if Config.GOD_MODE:
            return HTML(f'<style bg="{bg}" fg="{fg}"> > accept-edits mode: file edits auto-approved (shift+tab to cycle) </style>')
        else:
            return HTML(f'<style bg="{bg}" fg="{fg}"> > ask-before-edit mode: manual approval required (shift+tab to cycle) </style>')

    def get_rprompt_text(self):
        from prompt_toolkit.formatted_text import HTML
        from aether.cli.theme_engine import ThemeEngine
        theme = ThemeEngine.get_current_theme()
        
        bg = theme.get("secondary", "#bb9af7")
        fg = theme.get("bg", "#1a1b26")
        
        mode_str = "accept-edits" if Config.GOD_MODE else "ask-before-edit"
        return HTML(f'<style bg="{bg}" fg="{fg}"> ? for shortcuts · {mode_str} · {self.model} · high </style>')

def toggle_mode(event=None):
    from aether.config import Config
    Config.GOD_MODE = not Config.GOD_MODE

