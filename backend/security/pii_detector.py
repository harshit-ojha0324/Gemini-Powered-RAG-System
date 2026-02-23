from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PIIDetector:
    def __init__(self):
        self.analyzer: Optional[AnalyzerEngine] = None
        self.anonymizer: Optional[AnonymizerEngine] = None
        self.analyzer_available: bool = False
        
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.analyzer_available = True
            logger.info("✅ PII Detector initialized with spacy model")
        except Exception as e:
            logger.warning(f"⚠️  PII Detector spacy model unavailable: {str(e)}")
            logger.warning("Will use pattern-based PII detection only")
        
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        }
    
    def detect(self, text: str) -> Dict:
        """Detect PII in text"""
        results = {"has_pii": False, "types": [], "entities": []}
        
        # Try analyzer-based detection first if available
        if self.analyzer_available and self.analyzer is not None:
            try:
                analyzer_results = self.analyzer.analyze(
                    text=text, language="en",
                    entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", 
                             "CREDIT_CARD", "US_SSN", "US_PASSPORT",
                             "IBAN_CODE", "IP_ADDRESS"]
                )
                
                if analyzer_results:
                    results["has_pii"] = True
                    for result in analyzer_results:
                        results["types"].append(result.entity_type)
                        results["entities"].append({
                            "type": result.entity_type,
                            "text": text[result.start:result.end],
                            "score": result.score
                        })
            except Exception as e:
                logger.warning(f"Analyzer error: {str(e)}, falling back to patterns")
                self._pattern_based_detect(text, results)
        else:
            # Use pattern-based detection as fallback
            self._pattern_based_detect(text, results)
        
        return results
    
    def _pattern_based_detect(self, text: str, results: Dict) -> Dict:
        """Pattern-based PII detection as fallback"""
        for pii_type, pattern in self.patterns.items():
            if re.search(pattern, text):
                if pii_type.upper() not in results["types"]:
                    results["types"].append(pii_type.upper())
                    results["has_pii"] = True
        
        return results
    
    def anonymize(self, text: str) -> str:
        """Anonymize PII in text. Use analyzer when available, otherwise pattern-based."""
        if self.analyzer_available and self.analyzer is not None and self.anonymizer is not None:
            try:
                analyzer_results = self.analyzer.analyze(text=text, language="en")
                anonymized = self.anonymizer.anonymize(text=text, analyzer_results=analyzer_results)  # type: ignore
                return anonymized.text
            except Exception as e:
                logger.warning(f"Analyzer anonymize error: {e}. Falling back to patterns.")
        
        # Pattern-based fallback anonymization
        masked = text
        masked = re.sub(self.patterns["email"], "[EMAIL_REDACTED]", masked, flags=re.IGNORECASE)
        masked = re.sub(self.patterns["phone"], "[PHONE_REDACTED]", masked, flags=re.IGNORECASE)
        masked = re.sub(self.patterns["ssn"], "[SSN_REDACTED]", masked, flags=re.IGNORECASE)
        masked = re.sub(self.patterns["credit_card"], "[CREDIT_CARD_REDACTED]", masked, flags=re.IGNORECASE)
        return masked
    
    def redact(self, text: str, entity_types: Optional[List[str]] = None) -> str:
        """Redact specific PII types"""
        # If analyzer available, use it; otherwise fall back to pattern-based redaction
        if self.analyzer_available and self.analyzer is not None and self.anonymizer is not None:
            try:
                if entity_types is None:
                    entity_types = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN"]

                analyzer_results = self.analyzer.analyze(
                    text=text,
                    language="en",
                    entities=entity_types
                )

                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=analyzer_results,  # type: ignore
                    operators={"DEFAULT": {"type": "replace", "new_value": "[REDACTED]"}}  # type: ignore
                )

                return anonymized_result.text
            except Exception as e:
                logger.warning(f"Analyzer redact error: {e}. Falling back to patterns.")

        # Pattern-based redaction fallback
        redacted = text
        if entity_types is None:
            # redact common PII types
            redacted = re.sub(self.patterns["email"], "[REDACTED]", redacted, flags=re.IGNORECASE)
            redacted = re.sub(self.patterns["phone"], "[REDACTED]", redacted, flags=re.IGNORECASE)
            redacted = re.sub(self.patterns["ssn"], "[REDACTED]", redacted, flags=re.IGNORECASE)
            redacted = re.sub(self.patterns["credit_card"], "[REDACTED]", redacted, flags=re.IGNORECASE)
        else:
            # Map entity type names to patterns where possible
            mapping = {
                "EMAIL_ADDRESS": self.patterns["email"],
                "PHONE_NUMBER": self.patterns["phone"],
                "US_SSN": self.patterns["ssn"],
                "CREDIT_CARD": self.patterns["credit_card"]
            }
            for et in entity_types:
                pat = mapping.get(et)
                if pat:
                    redacted = re.sub(pat, "[REDACTED]", redacted, flags=re.IGNORECASE)

        return redacted