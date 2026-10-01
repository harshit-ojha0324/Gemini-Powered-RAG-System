from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# Identifiers a document question never needs to send to the LLM. PERSON is
# deliberately absent: names are what people ask their documents about.
ENTITIES = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN",
            "US_PASSPORT", "IBAN_CODE", "IP_ADDRESS"]

# Regex fallback for when Presidio's spaCy model is unavailable. Longest
# digit patterns first so a phone match can't eat part of a card number.
PATTERNS = {
    "EMAIL_ADDRESS": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    "CREDIT_CARD": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    "US_SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    "PHONE_NUMBER": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
}

REDACT = {"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})}


class PIIDetector:
    def __init__(self):
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("✅ PII Detector initialized with spacy model")
        except Exception as e:
            self.analyzer = None
            logger.warning(f"⚠️  PII Detector spacy model unavailable: {str(e)}")
            logger.warning("Will use pattern-based PII detection only")

    def redact(self, text: str) -> Tuple[str, List[str]]:
        """Replace PII with [REDACTED]; return the redacted text and the PII types found."""
        if self.analyzer is not None:
            try:
                results = self.analyzer.analyze(text=text, language="en", entities=ENTITIES)
                redacted = self.anonymizer.anonymize(
                    text=text, analyzer_results=results, operators=REDACT  # type: ignore[arg-type]
                ).text
                return redacted, sorted({r.entity_type for r in results})
            except Exception as e:
                logger.warning(f"Analyzer error: {e}. Falling back to patterns.")

        types = []
        for pii_type, pattern in PATTERNS.items():
            text, count = re.subn(pattern, "[REDACTED]", text)
            if count:
                types.append(pii_type)
        return text, types
