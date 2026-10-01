import re
from typing import Dict

class InputValidator:
    def __init__(self):
        self.sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)"
        ]
        
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
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"<iframe",
            r"eval\("
        ]
    
    def validate(self, text: str) -> Dict:
        """Validate input for security threats"""
        warnings = []
        is_valid = True
        
        if len(text) > 10000:
            warnings.append("INPUT_TOO_LONG")
            is_valid = False
        
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("INJECTION_SQL_DETECTED")
                is_valid = False
                break
        
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("INJECTION_PROMPT_DETECTED")
                is_valid = False
                break
        
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("INJECTION_XSS_DETECTED")
                is_valid = False
                break
        
        special_char_ratio = sum(not c.isalnum() and not c.isspace() for c in text) / max(len(text), 1)
        if special_char_ratio > 0.3:
            warnings.append("SUSPICIOUS_CHARACTERS")
        
        return {
            "is_valid": is_valid,
            "warnings": warnings
        }