"""Intent Classifier — rule-based intent detection and entity extraction.

This module uses keyword matching to classify user messages into
predefined intents and extracts relevant entities (FIR numbers,
names, dates, etc.) from the message text.

Responsibilities:
  - Classify intent (no LLM, no SQL)
  - Extract entities (FIR numbers, names, IDs, etc.)
  - Return confidence scores

Version: 2.0 (Hybrid SQL + LLM)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IntentResult:
    """Result of intent classification with extracted entities."""
    intent: str
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)


# ─── Intent Keyword Patterns ────────────────────────────────────
# Ordered by specificity — specific patterns checked first

INTENT_PATTERNS: list[tuple[str, float, list[str]]] = [
    # ── Case/Investigation Support ──────────────────────────────
    ("CASE_SUMMARY", 0.98, [
        "summarize case", "case summary", "investigation summary",
        "full case details", "case overview",
    ]),
    ("REPORT_GENERATION", 0.97, [
        "generate report", "create report", "officer report",
        "executive report", "daily report", "weekly report",
    ]),

    # ── FIR ─────────────────────────────────────────────────────
    ("FIR_SUMMARY", 0.96, [
        "summarize fir", "summary of fir", "explain fir",
        "fir explanation", "tell me about fir", "fir brief",
    ]),
    ("FIR_CREATE", 0.95, [
        "create fir", "register fir", "new fir", "file fir",
    ]),
    ("FIR_UPDATE", 0.95, [
        "update fir", "edit fir", "modify fir",
    ]),
    ("FIR_SEARCH", 0.90, [
        "show fir", "find fir", "search fir", "fir details",
        "display fir", "get fir", "fir number", "fir status",
        "check fir", "list firs", "all firs",
    ]),

    # ── Victims ─────────────────────────────────────────────────
    ("VICTIM_SUMMARY", 0.96, [
        "victim summary", "summarize victim", "explain victim",
    ]),
    ("VICTIM_CREATE", 0.95, [
        "add victim", "create victim", "register victim",
    ]),
    ("VICTIM_SEARCH", 0.90, [
        "show victim", "find victim", "victim details",
        "list victims", "search victim", "victim information",
    ]),

    # ── Accused ─────────────────────────────────────────────────
    ("ACCUSED_SUMMARY", 0.96, [
        "accused summary", "summarize accused", "explain accused",
    ]),
    ("ACCUSED_CREATE", 0.95, [
        "add accused", "register accused", "create accused",
    ]),
    ("ACCUSED_SEARCH", 0.90, [
        "show accused", "find accused", "accused details",
        "list accused", "search accused", "accused information",
    ]),

    # ── Evidence ────────────────────────────────────────────────
    ("EVIDENCE_SUMMARY", 0.96, [
        "summarize evidence", "explain evidence", "evidence summary",
    ]),
    ("EVIDENCE_CREATE", 0.95, [
        "add evidence", "upload evidence", "submit evidence",
    ]),
    ("EVIDENCE_SEARCH", 0.90, [
        "show evidence", "find evidence", "evidence details",
        "list evidence", "search evidence",
    ]),

    # ── Financial Transactions ──────────────────────────────────
    ("FINANCIAL_SUMMARY", 0.96, [
        "suspicious transaction", "analyze transaction",
        "transaction summary", "explain transaction",
    ]),
    ("FINANCIAL_SEARCH", 0.90, [
        "show transaction", "financial transaction",
        "bank transaction", "list transactions",
    ]),

    # ── Crime History ───────────────────────────────────────────
    ("CRIME_HISTORY_SUMMARY", 0.96, [
        "history summary", "summarize history", "explain history",
    ]),
    ("CRIME_HISTORY_SEARCH", 0.90, [
        "crime history", "previous crimes", "criminal history",
        "list history", "search history",
    ]),

    # ── Hotspots ────────────────────────────────────────────────
    ("HOTSPOT_ANALYSIS", 0.96, [
        "hotspot analysis", "hotspot trend", "explain hotspot",
        "crime concentration", "analyze hotspot",
    ]),
    ("HOTSPOT_SEARCH", 0.90, [
        "crime hotspot", "show hotspot", "hotspot areas",
        "high crime area",
    ]),

    # ── Criminal Network ────────────────────────────────────────
    ("NETWORK_ANALYSIS", 0.96, [
        "explain network", "network analysis", "relationship analysis",
        "analyze network", "criminal connections",
    ]),
    ("NETWORK_SEARCH", 0.90, [
        "criminal network", "show network", "network graph",
        "find connections",
    ]),

    # ── Location ────────────────────────────────────────────────
    ("LOCATION_SEARCH", 0.90, [
        "show location", "find location", "search location",
        "location details", "list locations",
    ]),

    # ── Audit Log ───────────────────────────────────────────────
    ("AUDIT_SEARCH", 0.90, [
        "audit logs", "system logs", "activity logs",
        "user activity", "search logs",
    ]),

    # ── Users ───────────────────────────────────────────────────
    ("USER_SEARCH", 0.90, [
        "show users", "list users", "user information",
        "search user", "find user", "user details",
    ]),

    # ── Settings ────────────────────────────────────────────────
    ("SETTINGS", 0.88, [
        "settings", "preferences", "profile settings",
        "configure",
    ]),

    # ── Crime Prediction ────────────────────────────────────────
    ("CRIME_PREDICTION", 0.95, [
        "predict crime", "crime prediction", "future crime",
        "crime forecast", "prediction analysis",
    ]),

    # ── General Help ────────────────────────────────────────────
    ("HELP", 0.85, [
        "help", "what can you do", "capabilities",
        "commands", "how to", "what are",
    ]),
]


# ─── Entity Extraction Patterns ─────────────────────────────────

def extract_entities(message: str) -> dict[str, str]:
    """Extract structured entities (FIR numbers, names, IDs) from the message.

    Returns a dict of entity_type → entity_value.
    """
    entities: dict[str, str] = {}
    text = message.strip()

    # FIR number patterns: FIR-2026-00001, FIR12345, #12345
    fir_match = re.search(r"(?:FIR)[-\s]?(\d+)", text, re.IGNORECASE)
    if fir_match:
        entities["fir_number"] = fir_match.group(0)
        entities["fir_id"] = fir_match.group(1)

    # Simple numeric ID pattern (if no FIR match)
    id_match = re.search(r"(?:#|ID\s*:|id\s*:)?\s*(\d{4,})", text)
    if id_match and "fir_id" not in entities:
        entities["reference_id"] = id_match.group(1)

    # Phone number (10 digits)
    phone_match = re.search(r"\b(\d{10})\b", text)
    if phone_match:
        entities["phone"] = phone_match.group(1)

    # Email address
    email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text)
    if email_match:
        entities["email"] = email_match.group(0)

    # Name patterns (after keywords like "about", "for", "named")
    name_match = re.search(r"(?:about|for|named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text)
    if name_match:
        entities["name"] = name_match.group(1)

    # Date patterns (DD/MM/YYYY, YYYY-MM-DD)
    date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if date_match:
        entities["date"] = date_match.group(1)

    return entities


def classify_intent(message: str) -> IntentResult:
    """Classify a user message into an intent.

    Uses ordered keyword matching with confidence scoring.
    Returns the best matching intent with extracted entities.

    Args:
        message: The user's message text.

    Returns:
        IntentResult with intent name, confidence score, and extracted entities.
    """
    text = message.lower().strip()

    # Extract entities first
    entities = extract_entities(message)

    # Match against ordered intent patterns (most specific first)
    for intent_name, confidence, keywords in INTENT_PATTERNS:
        for keyword in keywords:
            if keyword in text:
                return IntentResult(
                    intent=intent_name,
                    confidence=confidence,
                    entities=entities,
                )

    # Fallback — no keyword matched, check extracted entities
    if "fir_id" in entities or "fir_number" in entities:
        return IntentResult(
            intent="FIR_SEARCH",
            confidence=0.85,
            entities=entities,
        )
    if "phone" in entities:
        # Could be accused or victim search — default to accused
        return IntentResult(
            intent="ACCUSED_SEARCH",
            confidence=0.70,
            entities=entities,
        )
    if "email" in entities:
        return IntentResult(
            intent="USER_SEARCH",
            confidence=0.70,
            entities=entities,
        )

    # Truly unmatched — return GENERAL_CHAT
    return IntentResult(
        intent="GENERAL_CHAT",
        confidence=0.40,
        entities=entities,
    )


def intent_requires_ai(intent_name: str) -> bool:
    """Return True if the intent requires AI summarization via Gemini.

    Search and CRUD operations use MySQL directly (no AI).
    Summary, analysis, and report intents use Gemini for NL generation.
    """
    ai_intents = {
        "FIR_SUMMARY", "VICTIM_SUMMARY", "ACCUSED_SUMMARY",
        "EVIDENCE_SUMMARY", "FINANCIAL_SUMMARY",
        "CRIME_HISTORY_SUMMARY", "HOTSPOT_ANALYSIS",
        "NETWORK_ANALYSIS", "CRIME_PREDICTION",
        "REPORT_GENERATION", "CASE_SUMMARY",
    }
    return intent_name in ai_intents
