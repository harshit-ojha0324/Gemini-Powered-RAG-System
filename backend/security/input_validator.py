import re
from typing import Dict

class InputValidator:
    # No SQL or XSS patterns: questions never reach a SQL engine or an HTML
    # sink (Chroma filters are built server-side, React escapes all output),
    # and those patterns blocked ordinary questions like "Which plan covers C#?".
    def __init__(self):
        self.prompt_injection_patterns = [
            r"ignore .*?(instructions|prompts|rules)",
            r"disregard .*?(instructions|prompts|rules)",
            r"forget .*?(instructions|prompts|rules)",
            r"you are now",
            r"new .*?(instructions|rules|role)",
            r"system prompt",
            r"override .*?(instructions|settings|rules)",
            r"jailbreak",
            r"do anything now",
            r"\bdan\b"
        ]

    def validate(self, text: str) -> Dict:
        """Validate input for security threats"""
        warnings = []
        is_valid = True
        
        if len(text) > 10000:
            warnings.append("INPUT_TOO_LONG")
            is_valid = False
        
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("INJECTION_PROMPT_DETECTED")
                is_valid = False
                break

        special_char_ratio = sum(not c.isalnum() and not c.isspace() for c in text) / max(len(text), 1)
        if special_char_ratio > 0.3:
            warnings.append("SUSPICIOUS_CHARACTERS")
        
        return {
            "is_valid": is_valid,
            "warnings": warnings
        }