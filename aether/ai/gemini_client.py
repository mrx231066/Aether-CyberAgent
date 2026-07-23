# Yellow Team: AI Remediation Engine
# Uses Google Gemini API via google-genai SDK

import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from rich.console import Console

console = Console()


class RemediationResult(BaseModel):
    """Structured output schema for Gemini remediation patches."""
    vulnerability_title: str = Field(description="Title of the vulnerability found")
    severity_level: str = Field(description="Severity: CRITICAL, HIGH, MEDIUM, LOW")
    patched_code: str = Field(description="The complete patched source code")
    fix_rationale: str = Field(description="Explanation of why this fix is secure")


class GeminiClient:
    """Yellow Team: Interfaces with Google Gemini 2.5 Flash for code remediation.
    
    Uses structured outputs via Pydantic to ensure type-safe, deterministic
    response parsing from the LLM.
    """
    
    MODEL = "gemini-2.5-flash"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it via environment variable "
                "or pass api_key to GeminiClient()."
            )
        self.client = genai.Client(api_key=self.api_key)
    
    def request_patch(
        self,
        source_code: str,
        blue_team_report: dict,
        previous_failure_trace: Optional[str] = None,
    ) -> RemediationResult:
        """Request a security patch from Gemini based on Blue Team findings.
        
        Args:
            source_code: The original vulnerable source code.
            blue_team_report: Dictionary containing Blue Team audit findings.
            previous_failure_trace: If this is a retry from Gold Team,
                the error trace from the Purple Team verification failure.
        
        Returns:
            RemediationResult with the patched code and metadata.
        """
        prompt = self._build_prompt(source_code, blue_team_report, previous_failure_trace)
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RemediationResult,
            temperature=0.2,  # Low temp for deterministic security patches
        )
        
        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
            config=config,
        )
        
        # Parse the structured JSON response into our Pydantic model
        result = RemediationResult.model_validate_json(response.text)
        return result
    
    def _build_prompt(
        self,
        source_code: str,
        blue_team_report: dict,
        previous_failure_trace: Optional[str] = None,
    ) -> str:
        """Build the remediation prompt for Gemini."""
        prompt_parts = [
            "You are an elite security engineer. Your task is to fix the following "
            "vulnerable Python code based on the security audit report below.",
            "",
            "## VULNERABLE SOURCE CODE",
            "```python",
            source_code,
            "```",
            "",
            "## BLUE TEAM AUDIT REPORT",
            json.dumps(blue_team_report, indent=2),
            "",
            "## REQUIREMENTS",
            "1. Fix ALL identified vulnerabilities.",
            "2. Maintain the original code's functionality.",
            "3. Add proper type annotations to the patched code.",
            "4. Use secure alternatives (e.g., ast.literal_eval instead of eval, "
            "subprocess.run with shell=False instead of shell=True).",
            "5. Return the COMPLETE patched file, not just the changed lines.",
        ]
        
        if previous_failure_trace:
            prompt_parts.extend([
                "",
                "## ⚠️ PREVIOUS ATTEMPT FAILED VERIFICATION",
                "Your last patch failed formal verification with this error:",
                previous_failure_trace,
                "",
                "Fix the issues identified above in your new patch.",
            ])
        
        return "\n".join(prompt_parts)
