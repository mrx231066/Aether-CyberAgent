"""Yellow Team: Autonomous Developer & Script Generator Agent.

Uses Google Gemini with function-calling to plan solutions,
write code, create scripts, and invoke tools autonomously.
"""

import os
import json
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm

from aether.engine.tools import ToolEngine

console = Console()


# ── Tool Declarations for Gemini Function Calling ──

TOOL_DECLARATIONS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="read_file",
            description="Read the contents of a file at the given path.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "file_path": types.Schema(
                        type="STRING",
                        description="Path to the file to read",
                    ),
                },
                required=["file_path"],
            ),
        ),
        types.FunctionDeclaration(
            name="write_file",
            description="Write content to a file, creating parent directories if needed. "
                        "Always provide the complete file contents.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "file_path": types.Schema(
                        type="STRING",
                        description="Path to write the file",
                    ),
                    "content": types.Schema(
                        type="STRING",
                        description="Complete file content to write",
                    ),
                },
                required=["file_path", "content"],
            ),
        ),
        types.FunctionDeclaration(
            name="execute_shell",
            description="Execute a shell command and return stdout, stderr, and exit code. "
                        "Use for running scripts, tests, git commands, etc.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "command": types.Schema(
                        type="STRING",
                        description="Shell command to execute",
                    ),
                    "timeout": types.Schema(
                        type="INTEGER",
                        description="Timeout in seconds (default 30)",
                    ),
                },
                required=["command"],
            ),
        ),
        types.FunctionDeclaration(
            name="list_dir",
            description="List the contents of a directory as a tree structure.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "path": types.Schema(
                        type="STRING",
                        description="Directory path to list (default: current directory)",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="adb_connector",
            description="Execute Android Debug Bridge commands (adb devices, adb shell). Auto-bridges if offline.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "command": types.Schema(
                        type="STRING",
                        description="ADB command to execute (without 'adb ' prefix)",
                    ),
                },
                required=["command"],
            ),
        ),
        types.FunctionDeclaration(
            name="github_connector",
            description="Interface with local Git CLI to read status, commit, and push dynamically.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "action": types.Schema(
                        type="STRING",
                        description="Git action: status, add, commit, push",
                    ),
                    "target": types.Schema(
                        type="STRING",
                        description="Target file for add, or commit message for commit",
                    ),
                },
                required=["action"],
            ),
        ),
        types.FunctionDeclaration(
            name="gmail_connector",
            description="Stub function for future email integrations.",
        ),
    ]),
]


class YellowPatcher:
    """Yellow Team: Autonomous Developer Agent with tool-calling capabilities.

    Uses Gemini function calling to read files, write code, execute commands,
    and inspect project structure autonomously.
    """

    SYSTEM_PROMPT = (
        "You are Aether, an elite AI security engineer and autonomous developer agent. "
        "You have access to tools for reading files, writing files, executing shell commands, "
        "and listing directories. Use these tools to help the user with coding, security, "
        "and development tasks.\n\n"
        "Guidelines:\n"
        "- Explain what you're doing and why before taking action.\n"
        "- When writing or modifying code, show a summary of changes.\n"
        "- For security tasks, use defensive best practices.\n"
        "- Never use eval(), exec(), or shell=True in generated code.\n"
        "- Use proper type annotations and error handling in all code."
    )

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")
        self.model = model or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
        self.client = genai.Client(api_key=self.api_key)
        self.tools = ToolEngine()
        self._init_chat()

    def _init_chat(self) -> None:
        """Initialize a persistent chat session with Gemini."""
        config = types.GenerateContentConfig(
            system_instruction=self.SYSTEM_PROMPT,
            tools=TOOL_DECLARATIONS,
            temperature=0.3,
        )
        self.chat_session = self.client.chats.create(
            model=self.model,
            config=config,
        )

    def chat(self, user_message: str) -> str:
        from aether.config import SessionState
        from PIL import Image
        from pathlib import Path
        
        # Phase 3: Vision Check
        contents = [user_message]
        for word in user_message.split():
            if word.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif')):
                img_path = Path(word).resolve()
                if img_path.exists() and img_path.is_file():
                    try:
                        img = Image.open(img_path)
                        contents.append(img)
                        console.print(f"[dim]👁️ Loaded vision context: {img_path.name}[/dim]")
                    except Exception as e:
                        console.print(f"[dim red]Vision Error: Could not load {img_path.name}: {e}[/dim red]")

        console.print(f"\n[bold cyan]🤖 Aether:[/bold cyan] ", end="")
        response_stream = self.chat_session.send_message_stream(contents)
        SessionState.chat_history.append(f"User: {user_message}")

        for _ in range(10):
            function_calls = []
            text_parts = []
            
            for chunk in response_stream:
                if chunk.usage_metadata:
                    # In newer google-genai versions it might be prompt_token_count + candidates_token_count
                    total = getattr(chunk.usage_metadata, "total_token_count", 0)
                    if total == 0:
                        p = getattr(chunk.usage_metadata, "prompt_token_count", 0)
                        c = getattr(chunk.usage_metadata, "candidates_token_count", 0)
                        total = p + c
                    SessionState.total_tokens += total
                    
                if not chunk.candidates:
                    continue
                    
                candidate = chunk.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            function_calls.append(part.function_call)
                        elif hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                            console.print(part.text, end="")

            if not function_calls:
                console.print()  # Newline after finished streaming text
                final_text = "\n".join(text_parts) if text_parts else "Task completed."
                SessionState.chat_history.append(f"Aether: {final_text}")
                return final_text

            console.print() # Newline before tool execution
            
            tool_responses = []
            for fc in function_calls:
                result = self._execute_tool(fc.name, dict(fc.args) if fc.args else {})
                tool_responses.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": result},
                    )
                )

            console.print(f"\n[bold cyan]🤖 Aether:[/bold cyan] ", end="")
            response_stream = self.chat_session.send_message_stream(tool_responses)

        return "Maximum tool execution rounds reached."

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as a string.

        Args:
            tool_name: Name of the tool to execute.
            args: Arguments for the tool.

        Returns:
            String result of the tool execution.
        """
        try:
            if tool_name == "read_file":
                content = self.tools.read_file(args["file_path"])
                console.print(f"[dim]📖 Read: {args['file_path']} ({len(content)} bytes)[/dim]")
                return content

            elif tool_name == "write_file":
                from aether.config import Config
                file_path = args["file_path"]
                content = args["content"]

                console.print(f"\n[bold yellow]📝 Agent wants to write: {file_path}[/bold yellow]")
                lang = "python" if file_path.endswith(".py") else "text"
                syntax = Syntax(content, lang, theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Proposed: {file_path}", border_style="yellow"))

                if Config.GOD_MODE or Confirm.ask(f"[bold]Apply changes to {file_path}?[/bold]", default=True):
                    self.tools.write_file(file_path, content)
                    console.print(f"[green]✅ Written: {file_path}[/green]")
                    return f"File written successfully: {file_path}"
                else:
                    console.print("[yellow]⏭️  Write skipped by user.[/yellow]")
                    return f"User declined to write {file_path}"

            elif tool_name == "execute_shell":
                command = args["command"]
                timeout = int(args.get("timeout", 30))
                console.print(f"[dim]⚡ Executing: {command}[/dim]")
                result = self.tools.execute_shell(command, timeout=timeout)

                if result["stdout"]:
                    console.print(Panel(
                        result["stdout"].strip()[:2000],
                        title="stdout", border_style="green",
                    ))
                if result["stderr"]:
                    console.print(Panel(
                        result["stderr"].strip()[:2000],
                        title="stderr", border_style="red",
                    ))

                return json.dumps(result)

            elif tool_name == "list_dir":
                path = args.get("path", ".")
                entries = self.tools.list_dir(path)
                tree_str = "\n".join(entries[:100])
                console.print(f"[dim]📁 Listed: {path} ({len(entries)} entries)[/dim]")
                return tree_str

            elif tool_name == "adb_connector":
                from aether.engine.connectors import adb_connector
                cmd = args["command"]
                console.print(f"[dim]📱 ADB Executing: {cmd}[/dim]")
                return adb_connector(cmd)

            elif tool_name == "github_connector":
                from aether.engine.connectors import github_connector
                action = args["action"]
                target = args.get("target", "")
                console.print(f"[dim]🐙 Git Action: {action} {target}[/dim]")
                return github_connector(action, target)

            elif tool_name == "gmail_connector":
                from aether.engine.connectors import gmail_connector
                console.print(f"[dim]📧 Gmail Connector Invoked[/dim]")
                return gmail_connector()

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            error_msg = f"Tool error ({tool_name}): {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            return error_msg

    def generate_script(self, task_description: str) -> Optional[str]:
        """Generate a Python script based on a task description.

        Args:
            task_description: Description of what the script should do.

        Returns:
            Generated script content, or None if generation failed.
        """
        prompt = (
            f"Generate a Python script for the following task:\n\n"
            f"{task_description}\n\n"
            f"Write the complete, runnable script. Use proper error handling "
            f"and type annotations. Do NOT use eval() or exec()."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )

        if response.text:
            text = response.text
            # Extract code block if wrapped in markdown fences
            if "```python" in text:
                start = text.index("```python") + len("```python")
                end = text.index("```", start)
                return text[start:end].strip()
            elif "```" in text:
                start = text.index("```") + 3
                end = text.index("```", start)
                return text[start:end].strip()
            return text

        return None
