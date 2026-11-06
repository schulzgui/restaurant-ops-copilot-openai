"""Defense in depth for a synthetic-only lab; not a complete DLP classifier."""
import json
import re
from .domain import DomainError

PATTERNS = [
    r"sk-[A-Za-z0-9_-]{8,}",
    r"(?i)bearer\s+[A-Za-z0-9._-]{8,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
    r"(?<!\d)(?:\+55[ -]?)?\(?\d{2}\)?[ -]?9?\d{4}[- ]?\d{4}(?!\d)",
]

def check_text(text):
    if any(re.search(pattern, text) for pattern in PATTERNS):
        raise DomainError("Possível dado pessoal ou credencial detectado; use apenas dados sintéticos e IDs SYN.")

def check_outbound(history):
    # Check semantic text, not generated UUID/call identifiers that may resemble phone numbers.
    for item in history:
        if item.get("role") == "user":
            check_text(str(item.get("content", "")))

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "policy_ids": {"type": "array", "items": {"type": "string"}},
        "order_ids": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "policy_ids", "order_ids", "limitations"],
    "additionalProperties": False,
}
