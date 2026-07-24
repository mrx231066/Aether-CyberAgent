"""Phase 5: Local skills loader."""
import os
from pathlib import Path
from rich.console import Console

console = Console()

class SkillsLoader:
    @classmethod
    def discover_skills(cls):
        skills_dir = Path.home() / ".aether" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        skills = []
        for file in skills_dir.glob("*.py"):
            skills.append(file.stem)
        for file in skills_dir.glob("*.yaml"):
            skills.append(file.stem)
            
        return skills
