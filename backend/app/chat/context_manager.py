"""Conversation Context Manager — tracks entities across chat turns.

Maintains lightweight in-memory context about the current conversation.
Stores only the most recently referenced entities per category.
Resolves pronouns and references ("it", "this FIR", "his", "her") using
previously retrieved entities.

Context is updated after every successful structured query from MySQL.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationContext:
    """Lightweight in-memory conversation context.

    Tracks the most recently referenced entities so the chatbot can
    resolve pronouns and implicit references in follow-up questions.

    All fields are optional strings containing entity identifiers
    (FIR numbers, names, IDs, etc.).
    """
    current_fir: Optional[str] = None
    current_victim: Optional[str] = None
    current_accused: Optional[str] = None
    current_evidence: Optional[str] = None
    current_financial: Optional[str] = None
    current_location: Optional[str] = None
    current_crime_type: Optional[str] = None
    current_investigation: Optional[str] = None

    _last_mentioned_entity: Optional[str] = field(default=None, repr=False)
    _last_mentioned_type: Optional[str] = field(default=None, repr=False)

    # ── Private helpers ─────────────────────────────────────────

    def _set_last_mentioned(self, entity: str, entity_type: str) -> None:
        """Track the most recently mentioned entity for 'it' resolution."""
        self._last_mentioned_entity = entity
        self._last_mentioned_type = entity_type

    # ── Pronoun Resolution ──────────────────────────────────────

    def resolve(self, message: str) -> str:
        """Resolve pronouns and implicit references in the message.

        Recognised patterns (in priority order):
          - "this/that FIR / case"     → current_fir
          - "this/that accused / suspect" → current_accused
          - "this/that victim / complainant" → current_victim
          - "this/that evidence / document" → current_evidence
          - "his…"                     → current_accused (possessive)
          - "her…"                     → current_victim (possessive)
          - "it"                       → _last_mentioned_entity
          - "this/that investigation / matter" → current_investigation or current_fir

        Returns the message with resolved references, or the original
        if no resolution was possible.
        """
        if not message or not message.strip():
            return message

        original = message
        message = message.strip()

        # "this FIR" / "that FIR" / "this case" → current_fir
        if re.search(r"\b(this|that)\s+(fir|case)\b", message, re.IGNORECASE):
            if self.current_fir:
                message = re.sub(
                    r"\b(this|that)\s+(fir|case)\b",
                    self.current_fir,
                    message,
                    flags=re.IGNORECASE,
                )

        # "this accused" / "that accused" → current_accused
        if re.search(r"\b(this|that)\s+(accused|suspect)\b", message, re.IGNORECASE):
            if self.current_accused:
                message = re.sub(
                    r"\b(this|that)\s+(accused|suspect)\b",
                    self.current_accused,
                    message,
                    flags=re.IGNORECASE,
                )

        # "this victim" / "that victim" → current_victim
        if re.search(r"\b(this|that)\s+(victim|complainant)\b", message, re.IGNORECASE):
            if self.current_victim:
                message = re.sub(
                    r"\b(this|that)\s+(victim|complainant)\b",
                    self.current_victim,
                    message,
                    flags=re.IGNORECASE,
                )

        # "this evidence" / "that evidence" → current_evidence
        if re.search(r"\b(this|that)\s+(evidence|document)\b", message, re.IGNORECASE):
            if self.current_evidence:
                message = re.sub(
                    r"\b(this|that)\s+(evidence|document)\b",
                    self.current_evidence,
                    message,
                    flags=re.IGNORECASE,
                )

        # "his …" → current_accused (possessive)
        if re.search(r"\bhis\b", message, re.IGNORECASE):
            if self.current_accused:
                message = re.sub(
                    r"\bhis\b",
                    f"{self.current_accused}'s",
                    message,
                    flags=re.IGNORECASE,
                )

        # "her …" → current_victim (possessive)
        if re.search(r"\bher\b", message, re.IGNORECASE):
            if self.current_victim:
                message = re.sub(
                    r"\bher\b",
                    f"{self.current_victim}'s",
                    message,
                    flags=re.IGNORECASE,
                )

        # Generic "it" → last mentioned entity
        if re.search(r"(?<![a-zA-Z])it(?![a-zA-Z])", message, re.IGNORECASE):
            if self._last_mentioned_entity:
                message = re.sub(
                    r"(?<![a-zA-Z])it(?![a-zA-Z])",
                    self._last_mentioned_entity,
                    message,
                    flags=re.IGNORECASE,
                )

        # "this investigation" / "this matter" → current_investigation or current_fir
        if re.search(r"\bthis\s+(investigation|matter)\b", message, re.IGNORECASE):
            entity = self.current_investigation or self.current_fir
            if entity:
                message = re.sub(
                    r"\bthis\s+(investigation|matter)\b",
                    entity,
                    message,
                    flags=re.IGNORECASE,
                )

        if message != original:
            logger.info("Context resolved", extra={
                "original": original[:100],
                "resolved": message[:100],
            })

        return message

    # ── Context Update ──────────────────────────────────────────

    def update(self, intent: str, data: dict) -> None:
        """Update conversation context from a service response.

        Called after every successful structured query from MySQL.
        Extracts entity identifiers from the response data and stores
        them for future pronoun resolution.
        """
        if not data:
            return

        intent_prefix = intent.split("_")[0] if "_" in intent else intent

        # FIR
        if intent_prefix == "FIR" or intent == "CASE_SUMMARY":
            firs = data.get("firs", data.get("fir", []))
            if isinstance(firs, list) and firs:
                fir_num = firs[0].get("fir_number")
                if fir_num:
                    self.current_fir = fir_num
                    self._set_last_mentioned(fir_num, "fir")
            elif isinstance(firs, dict):
                fir_num = firs.get("fir_number")
                if fir_num:
                    self.current_fir = fir_num
                    self._set_last_mentioned(fir_num, "fir")

        # Accused
        if intent_prefix == "ACCUSED":
            accused_list = data.get("accused", [])
            if isinstance(accused_list, list) and accused_list:
                name = (
                    accused_list[0].get("full_name")
                    or accused_list[0].get("name")
                    or accused_list[0].get("accused_name")
                )
                if name:
                    self.current_accused = name
                    self._set_last_mentioned(name, "accused")

        # Victim
        if intent_prefix == "VICTIM":
            victims_list = data.get("victims", [])
            if isinstance(victims_list, list) and victims_list:
                name = (
                    victims_list[0].get("full_name")
                    or victims_list[0].get("name")
                    or victims_list[0].get("victim_name")
                )
                if name:
                    self.current_victim = name
                    self._set_last_mentioned(name, "victim")

        # Evidence
        if intent_prefix == "EVIDENCE":
            evidence_list = data.get("evidence", [])
            if isinstance(evidence_list, list) and evidence_list:
                ev_name = (
                    evidence_list[0].get("evidence_name")
                    or evidence_list[0].get("name")
                    or evidence_list[0].get("evidence_id")
                )
                if ev_name:
                    self.current_evidence = ev_name
                    self._set_last_mentioned(ev_name, "evidence")

        # Financial
        if intent_prefix == "FINANCIAL":
            txs = data.get("transactions", [])
            if isinstance(txs, list) and txs:
                ref = (
                    txs[0].get("transaction_id")
                    or txs[0].get("reference_number")
                    or txs[0].get("bank_name")
                )
                if ref:
                    self.current_financial = str(ref)
                    self._set_last_mentioned(str(ref), "financial")

        # Location / Hotspot
        if intent_prefix in ("LOCATION", "HOTSPOT"):
            locs = data.get("locations", data.get("hotspots", []))
            if isinstance(locs, list) and locs:
                loc_name = (
                    locs[0].get("location_name")
                    or locs[0].get("name")
                    or locs[0].get("district")
                )
                if loc_name:
                    self.current_location = loc_name
                    self._set_last_mentioned(loc_name, "location")

        # Crime type
        if intent_prefix == "PREDICTION":
            crime_type = data.get("crime_type") or data.get("predicted_crime")
            if crime_type:
                self.current_crime_type = str(crime_type)
                self._set_last_mentioned(str(crime_type), "crime_type")

        # Network — store investigation/case reference
        if intent_prefix == "NETWORK" and "nodes" in data:
            label = data.get("case_id") or data.get("investigation_id")
            if label:
                self.current_investigation = str(label)
                self._set_last_mentioned(str(label), "investigation")

        # Criminal history
        if intent_prefix == "HISTORY":
            history_for = data.get("accused_name") or data.get("subject")
            if history_for:
                self.current_accused = history_for
                self._set_last_mentioned(history_for, "accused")

        logger.debug("Context updated", extra={
            "intent": intent,
            "fir": self.current_fir,
            "accused": self.current_accused,
            "victim": self.current_victim,
        })

    def clear(self) -> None:
        """Reset all context fields."""
        self.current_fir = None
        self.current_victim = None
        self.current_accused = None
        self.current_evidence = None
        self.current_financial = None
        self.current_location = None
        self.current_crime_type = None
        self.current_investigation = None
        self._last_mentioned_entity = None
        self._last_mentioned_type = None
        logger.debug("Context cleared")


# ─── Session-level Context Store ──────────────────────────────
# In-memory dict: conversation_id → ConversationContext
# This is intentionally NOT persisted to MySQL. Context is ephemeral
# and lives only for the lifetime of the server process.

_context_store: dict[int, ConversationContext] = {}


def get_context(conversation_id: int) -> ConversationContext:
    """Get or create a ConversationContext for the given conversation.

    This is the main entry point used by ChatService.
    """
    if conversation_id not in _context_store:
        _context_store[conversation_id] = ConversationContext()
        logger.debug("New context created", extra={"conversation_id": conversation_id})
    return _context_store[conversation_id]


def remove_context(conversation_id: int) -> None:
    """Remove context when a conversation is deleted."""
    if conversation_id in _context_store:
        del _context_store[conversation_id]
        logger.debug("Context removed", extra={"conversation_id": conversation_id})
