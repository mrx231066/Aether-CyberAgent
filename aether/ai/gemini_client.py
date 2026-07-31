# Yellow Team: AI Remediation Engine
# Uses Google Gemini API via google-genai SDK

import os
import json
from typing import Optional, List
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
    """Yellow Team: Interfaces with Google Gemini for code remediation.
    
    Uses structured outputs via Pydantic to ensure type-safe, deterministic
    response parsing from the LLM.
    """
    
    DEFAULT_MODEL = "gemini-3.1-pro-preview"
    DEFAULT_GEMINI_MODELS = [
        {
            "name": "gemini-3.1-pro-preview", 
            "info": "⭐ Recommended - Advanced Maths, Vibe Coding & Code Architecture"
        },
        {
            "name": "gemini-3.6-flash", 
            "info": "⚡ New - All-Around Fast Agentic Help"
        },
        {
            "name": "gemini-3.5-flash-lite", 
            "info": "🚀 New - Ultra-Fast High-Throughput Sub-Agent"
        },
    ]
    MODEL = DEFAULT_MODEL
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it via environment variable "
                "or pass api_key to GeminiClient()."
            )
        self.model = model or os.environ.get("GEMINI_MODEL") or self.DEFAULT_MODEL
        self.client = genai.Client(api_key=self.api_key)

    @classmethod
    def get_available_models(cls, api_key: Optional[str] = None) -> List[dict]:
        """Fetch available Gemini models dynamically using google-genai SDK."""
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            console.print("[yellow]⚠️  No API key provided for model discovery. Using default model list.[/yellow]")
            return cls.DEFAULT_GEMINI_MODELS

        try:
            client = genai.Client(api_key=key)
            models = list(client.models.list())
            discovered = []

            for m in models:
                name = getattr(m, "name", "") or ""
                actions = getattr(m, "supported_actions", None)
                if actions is None:
                    actions = getattr(m, "supported_generation_methods", []) or []

                actions_str = [str(a) for a in actions]
                supports_gen = any("generateContent" in a for a in actions_str) or not actions_str

                if supports_gen:
                    clean_name = name.replace("models/", "") if name.startswith("models/") else name
                    if clean_name.startswith("gemini-"):
                        if not any(d["name"] == clean_name for d in discovered):
                            discovered.append({"name": clean_name, "info": "Dynamically Verified"})

            if discovered:
                return discovered

            console.print("[yellow]⚠️  No compatible Gemini models found. Using default model list.[/yellow]")
            return cls.DEFAULT_GEMINI_MODELS

        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to fetch models dynamically: {e}. Using default model list.[/yellow]")
            return cls.DEFAULT_GEMINI_MODELS

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
            model=self.model,
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


# Alias for compatibility
GeminiSecurityClient = GeminiClient
