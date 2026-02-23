import re
from typing import Dict

class ContentFilter:
    def __init__(self):
        self.sensitive_patterns = {
            "api_key": r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9-_]{8,})',
            "password": r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
            "token": r'(token|auth)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9-_\.]{8,})',
            "aws_key": r'AKIA[0-9A-Z]{16}',
            "private_key": r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----'
        }
        
        self.harmful_keywords = [
            "instruction for making",
            "how to create illegal",
            "unauthorized access",
            "bypass security"
        ]
    
    def filter(self, text: str) -> str:
        """Filter sensitive content from output"""
        filtered_text = text
        
        for pattern_name, pattern in self.sensitive_patterns.items():
            filtered_text = re.sub(
                pattern,
                f"[{pattern_name.upper()}_REDACTED]",
                filtered_text,
                flags=re.IGNORECASE
            )
        
        return filtered_text
    
    def check_harmful_content(self, text: str) -> Dict:
        """Check for potentially harmful content"""
        flags = []
        
        for keyword in self.harmful_keywords:
            if keyword.lower() in text.lower():
                flags.append(keyword)
        
        return {
            "has_harmful_content": len(flags) > 0,
            "flags": flags
        }
    
    def moderate(self, text: str) -> Dict:
        """Complete moderation check"""
        return {
            "filtered_text": self.filter(text),
            "harmful_content": self.check_harmful_content(text),
            "original_length": len(text),
            "filtered_length": len(self.filter(text))
        }