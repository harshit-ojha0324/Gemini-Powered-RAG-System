import re

class ContentFilter:
    def __init__(self):
        self.sensitive_patterns = {
            "api_key": r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9-_]{8,})',
            "password": r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
            "token": r'(token|auth)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9-_\.]{8,})',
            "aws_key": r'AKIA[0-9A-Z]{16}',
            "private_key": r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----'
        }

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