"""Aether-CyberAgent: White Team SARIF Report Generator.

Converts the Gold Team's PipelineResult into a valid SARIF v2.1.0 JSON format.
"""

import json
from pathlib import Path
from typing import Any, Dict


class SarifReporter:
    """Generates SARIF v2.1.0 reports from pipeline results."""

    SCHEMA_URL = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json"
    VERSION = "2.1.0"
    DRIVER_NAME = "aether-cyberagent"
    DRIVER_VERSION = "0.1.0"

    def _map_severity(self, severity: str) -> str:
        """Map internal severity to SARIF level."""
        mapping = {
            "CRITICAL": "error",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
        }
        return mapping.get(severity.upper(), "warning")

    def generate_report(self, pipeline_result: Any) -> Dict[str, Any]:
        """Convert a PipelineResult into a SARIF report."""
        rules = {}
        results = []

        all_patches = getattr(pipeline_result, "verified_patches", []) + getattr(
            pipeline_result, "failed_patches", []
        )

        for patch in all_patches:
            findings = patch.get("findings", [])
            file_path = patch.get("file", "")

            for finding in findings:
                vuln_type = finding.get("type", "unknown_vulnerability")
                severity = finding.get("severity", "MEDIUM")
                level = self._map_severity(severity)
                message = finding.get("description", patch.get("vulnerability_title", vuln_type))
                line = finding.get("line", 1)

                if vuln_type not in rules:
                    rules[vuln_type] = {
                        "id": vuln_type,
                        "name": vuln_type.replace("_", " ").title(),
                        "shortDescription": {"text": f"{vuln_type} vulnerability"},
                        "defaultConfiguration": {"level": level},
                    }

                result = {
                    "ruleId": vuln_type,
                    "level": level,
                    "message": {"text": message},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": file_path},
                                "region": {"startLine": line},
                            }
                        }
                    ],
                }

                if patch in getattr(pipeline_result, "verified_patches", []):
                    result["fixes"] = [
                        {
                            "description": {"text": patch.get("fix_rationale", "Applied fix.")},
                            "artifactChanges": [
                                {
                                    "artifactLocation": {"uri": file_path},
                                    "replacements": [
                                        {
                                            "deletedRegion": {},
                                            "insertedContent": {"text": patch.get("patched_code", "")},
                                        }
                                    ],
                                }
                            ],
                        }
                    ]

                results.append(result)

        report = {
            "$schema": self.SCHEMA_URL,
            "version": self.VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.DRIVER_NAME,
                            "version": self.DRIVER_VERSION,
                            "rules": list(rules.values()),
                        }
                    },
                    "results": results,
                }
            ],
        }

        return report

    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """Save the SARIF report to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2))

    def export_from_pipeline(self, pipeline_result: Any, output_dir: str) -> str:
        """Generate and save the report, returning the file path."""
        report = self.generate_report(pipeline_result)
        
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        output_path = dir_path / "sarif_report.json"
        self.save_report(report, str(output_path))
        
        return str(output_path)
