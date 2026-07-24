"""Top Status Header (Command Bar) for Aether-CyberAgent."""

from aether.config import Config

class TopHeader:
    def __init__(self, model="Gemini 2.5 Pro"):
        self.model = model
        
    def get_header_text(self):
        from prompt_toolkit.formatted_text import HTML
        if Config.GOD_MODE:
            return HTML(f' <style bg="ansiyellow" fg="black"> > accept-edits mode: file edits auto-approved (shift+tab to cycle) ? for shortcuts | mode: accept-edits · {self.model} · high </style> ')
        else:
            return HTML(f' <style bg="ansiblue" fg="white"> > ask-before-edit mode: manual approval required (shift+tab to cycle) ? for shortcuts | mode: ask-before-edit · {self.model} · high </style> ')

def toggle_mode(event=None):
    from aether.config import Config
    Config.GOD_MODE = not Config.GOD_MODE
