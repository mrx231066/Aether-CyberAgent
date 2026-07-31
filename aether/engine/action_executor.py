"""Phase 4: Action Execution & Tag Parser Engine for Aether.

Parses structured action tags (<bash>, <python>, <read>, <write>, <patch>, <search>)
and executes them via ToolEngine with rich Live status indicators (yellow running, green success, red failure).
"""

import re
import sys
from typing import List, Dict, Any, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from aether.engine.tools import ToolEngine

console = Console()

class ActionExecutor:
    """Parses and executes action tags with live status indicators."""

    TAG_REGEX = re.compile(
        r"<(bash|python|read|search|write|patch)(?:\s+path=[\"']([^\"']+)[\"'])?\s*>(.*?)</\1>",
        re.DOTALL | re.IGNORECASE
    )

    def __init__(self, tools: Optional[ToolEngine] = None):
        self.tools = tools or ToolEngine()

    @classmethod
    def extract_actions(cls, text: str) -> List[Dict[str, Any]]:
        """Extract all structured action tags from response text."""
        actions = []
        for match in cls.TAG_REGEX.finditer(text):
            tag_type = match.group(1).lower()
            path_arg = match.group(2) or ""
            content = match.group(3).strip()
            actions.append({
                "type": tag_type,
                "path": path_arg,
                "content": content,
                "full_match": match.group(0)
            })
        return actions

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single extracted action tag with live status updates."""
        act_type = action["type"]
        content = action["content"]
        path_arg = action["path"]

        # Yellow dot status while running
        console.print(f"\n[bold yellow]●[/bold yellow] [dim]🟡 Running {act_type.upper()}: {content[:80]}[/dim]")

        result_data = {
            "type": act_type,
            "command": content,
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "success": True
        }

        if act_type == "bash":
            res = self.tools.execute_shell(content)
            result_data["stdout"] = res.get("stdout", "")
            result_data["stderr"] = res.get("stderr", "")
            result_data["exit_code"] = res.get("exit_code", 0)
            result_data["success"] = (res.get("exit_code") == 0)

            if result_data["success"]:
                console.print("[bold green]🟢 Success[/bold green]")
                if result_data["stdout"]:
                    console.print(Panel(result_data["stdout"].strip(), title="stdout", border_style="green"))
            else:
                console.print(f"[bold red]🔴 Failed (exit code {result_data['exit_code']})[/bold red]")
                if result_data["stderr"]:
                    console.print(Panel(result_data["stderr"].strip(), title="stderr", border_style="red"))

        elif act_type == "python":
            temp_script = self.tools.working_dir / ".aether_tmp.py"
            self.tools.write_file(str(temp_script), content)
            res = self.tools.execute_shell(f"python {temp_script}")
            result_data["stdout"] = res.get("stdout", "")
            result_data["stderr"] = res.get("stderr", "")
            result_data["exit_code"] = res.get("exit_code", 0)
            result_data["success"] = (res.get("exit_code") == 0)

            if result_data["success"]:
                console.print("[bold green]🟢 Success[/bold green]")
                if result_data["stdout"]:
                    console.print(Panel(result_data["stdout"].strip(), title="stdout", border_style="green"))
            else:
                console.print(f"[bold red]🔴 Failed (exit code {result_data['exit_code']})[/bold red]")
                if result_data["stderr"]:
                    console.print(Panel(result_data["stderr"].strip(), title="stderr", border_style="red"))

        elif act_type == "read":
            try:
                out = self.tools.read_file(content or path_arg)
                result_data["stdout"] = out
                console.print("[bold green]🟢 Success[/bold green]")
                console.print(Panel(out[:1000] + ("..." if len(out) > 1000 else ""), title=f"file: {content or path_arg}", border_style="green"))
            except Exception as e:
                result_data["stderr"] = str(e)
                result_data["exit_code"] = -1
                result_data["success"] = False
                console.print(f"[bold red]🔴 Failed: {e}[/bold red]")

        elif act_type == "write":
            target_path = path_arg or content.split("\n", 1)[0].strip()
            file_content = content if path_arg else (content.split("\n", 1)[1] if "\n" in content else "")
            try:
                self.tools.write_file(target_path, file_content)
                result_data["stdout"] = f"Wrote {len(file_content)} bytes to {target_path}"
                console.print("[bold green]🟢 Success[/bold green]")
            except Exception as e:
                result_data["stderr"] = str(e)
                result_data["exit_code"] = -1
                result_data["success"] = False
                console.print(f"[bold red]🔴 Failed: {e}[/bold red]")

        elif act_type == "search":
            res = self.tools.execute_shell(f"grep -rn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=node_modules '{content}' .")
            result_data["stdout"] = res.get("stdout", "")
            result_data["stderr"] = res.get("stderr", "")
            result_data["exit_code"] = res.get("exit_code", 0)
            result_data["success"] = (res.get("exit_code") == 0)
            if result_data["success"]:
                console.print("[bold green]🟢 Success[/bold green]")
                if result_data["stdout"]:
                    console.print(Panel(result_data["stdout"].strip(), title="search results", border_style="green"))
            else:
                console.print("[bold red]🔴 Failed[/bold red]")

        return result_data

    def process_and_execute_response(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract and execute all action tags found in the response."""
        actions = self.extract_actions(text)
        results = []
        for action in actions:
            res = self.execute_action(action)
            results.append(res)
        return text, results
