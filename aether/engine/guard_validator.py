"""Phase 4: Runtime Command Execution Guard & Response Validator for Aether.

Inspects agent responses before showing to user. If response contains unexecuted shell
commands in text/markdown fences without tool or action tag execution, intercepts and forces retry.
"""

import re
from typing import Tuple, List, Dict, Any

class CommandGuardValidator:
    """Validator enforcing that action-required requests are executed rather than printed."""

    UNEXECUTED_SHELL_REGEX = re.compile(
        r"```(?:bash|sh|shell|zsh)?\s*.*?(?:pkg|apt|npm|pip|git|rm|curl|chmod|pkill|mkdir|cd|python|systemctl|dpkg|tar|unzip|cat|touch|echo)\b.*?```",
        re.DOTALL | re.IGNORECASE
    )

    COMMAND_PATTERN_REGEX = re.compile(
        r"\b(?:pkg|apt|npm|pip|git|rm|curl|chmod|pkill|mkdir|systemctl|dpkg)\s+[a-zA-Z0-9_\-\.\/]+",
        re.IGNORECASE
    )

    @classmethod
    def validate_turn(cls, text: str, executed_actions: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Validate whether the turn executed required commands or illegally printed them as text.

        Returns:
            (is_valid, reason)
        """
        # If tool calls or action tags were executed during this turn, validation passes
        if len(executed_actions) > 0:
            return True, "Actions executed successfully."

        # Check if the text contains fenced code blocks with shell commands
        has_fenced_commands = bool(cls.UNEXECUTED_SHELL_REGEX.search(text))
        has_command_patterns = bool(cls.COMMAND_PATTERN_REGEX.search(text))

        if has_fenced_commands or has_command_patterns:
            return False, "Unexecuted shell commands detected in response text without tool execution."

        return True, "Response contains no unexecuted command requirements."

    @classmethod
    def get_retry_prompt(cls) -> str:
        """Returns the internal re-prompt when unexecuted commands are detected."""
        return (
            "You printed commands instead of executing them. Execute each command now "
            "using the shell tool or <bash>command</bash> tags, one at a time, and report the real output."
        )
