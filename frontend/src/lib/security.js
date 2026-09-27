// Plain-language names for the codes the backend logs
// (backend/security/input_validator.py and the PII check in backend/app.py).
const FLAG_LABELS = {
  INJECTION_SQL_DETECTED: 'SQL injection',
  INJECTION_PROMPT_DETECTED: 'Prompt injection',
  INJECTION_XSS_DETECTED: 'Script injection',
  INPUT_TOO_LONG: 'Question too long',
  SUSPICIOUS_CHARACTERS: 'Unusual characters',
  PII_DETECTED: 'Personal data',
};

// Notices for warnings on questions that were answered anyway.
const FLAG_NOTICES = {
  INPUT_TOO_LONG: 'Flagged as unusually long and recorded in the security log.',
  SUSPICIOUS_CHARACTERS: 'Flagged for unusual characters and recorded in the security log.',
};

// Entity names from Presidio and from the regex fallback.
const PII_NAMES = {
  EMAIL: 'an email address',
  EMAIL_ADDRESS: 'an email address',
  PHONE: 'a phone number',
  PHONE_NUMBER: 'a phone number',
  SSN: 'a Social Security number',
  US_SSN: 'a Social Security number',
  CREDIT_CARD: 'a card number',
  PERSON: 'a name',
  US_PASSPORT: 'a passport number',
  IBAN_CODE: 'a bank account number',
  IP_ADDRESS: 'an IP address',
};

const OUTCOME_LABELS = {
  blocked: 'Blocked',
  redacted: 'Redacted',
  flagged: 'Flagged',
};

function humanizeCode(code) {
  const text = String(code).toLowerCase().replace(/_/g, ' ').trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function joinList(items) {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

export function flagLabel(code) {
  return FLAG_LABELS[code] || humanizeCode(code);
}

/** Injection flags make the backend refuse the question outright. */
export function isBlockingFlag(code) {
  return String(code).startsWith('INJECTION');
}

export function eventOutcome(event) {
  if ((event.flags || []).some(isBlockingFlag)) return 'blocked';
  if (event.pii_detected) return 'redacted';
  return 'flagged';
}

export function outcomeLabel(outcome) {
  return OUTCOME_LABELS[outcome] || humanizeCode(outcome);
}

/** Turn the `security_warnings` on an answer into short notices. */
export function describeWarnings(warnings = []) {
  return warnings.map((warning) => {
    const pii = /^PII detected and redacted:\s*(.+)$/i.exec(warning);
    if (pii) {
      const kinds = [
        ...new Set(
          pii[1]
            .split(',')
            .map((type) => type.trim())
            .filter(Boolean)
            .map((type) => PII_NAMES[type.toUpperCase()] || humanizeCode(type).toLowerCase())
        ),
      ];
      return {
        kind: 'redacted',
        text: `Redacted ${joinList(kinds) || 'personal data'} before your question was sent to Gemini.`,
      };
    }
    return {
      kind: 'flagged',
      text: FLAG_NOTICES[warning] || `Flagged: ${flagLabel(warning)}.`,
    };
  });
}

const REDACTION_TOKEN = /\[(?:[A-Z]+_)*REDACTED\]/g;

/** Split text around "[REDACTED]"-style tokens so they can be drawn as bars. */
export function splitRedactions(text) {
  const parts = [];
  let last = 0;
  for (const match of String(text).matchAll(REDACTION_TOKEN)) {
    if (match.index > last) parts.push({ redacted: false, text: text.slice(last, match.index) });
    parts.push({ redacted: true, text: match[0] });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ redacted: false, text: text.slice(last) });
  return parts;
}
