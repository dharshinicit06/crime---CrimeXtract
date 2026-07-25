"""Chat Service — orchestrator for the Hybrid SQL + LLM architecture.

This module is the central orchestrator. It coordinates the flow:
    1. Receive user message
    2. If Kannada, translate to English (via Gemini translation helper)
    3. Resolve pronouns/references using conversation context
    4. Classify intent (rule-based, no LLM)
    5. Route to the correct module service via ServiceRouter
    6. Update conversation context with retrieved entities
    7. Optionally call Gemini for summarization/reasoning (only on structured data)
    8. If Kannada, translate response back to Kannada
    9. Build standardized response via ResponseBuilder
   10. Persist conversation history

The ChatService NEVER performs SQL queries directly.
It delegates to ServiceRouter → existing module services.
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.context_manager import ConversationContext, get_context
from app.chat.explanation_builder import ExplanationBuilder
from app.chat.gemini_service import GeminiService
from app.chat.timeline_service import InvestigationTimeline
from app.chat.recommendation_engine import RecommendationEngine
from app.chat.intent_classifier import (
    classify_intent,
    intent_requires_ai,
)
from app.chat.models import ChatAttachment
from app.chat.repository import ChatRepository
from app.chat.demo_router import DemoRouter
from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatRequest, ChatResponse
from app.chat.service_router import ServiceRouter
from app.chat.translator import TranslationService
from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


# ─── Follow-up Suggestions ──────────────────────────────────────

_FOLLOWUP_MAP: dict[str, list[str]] = {
    "FIR": ["Find related accused", "Show evidence for this FIR", "Generate a case summary"],
    "VICTIM": ["Find accused related to this victim", "Search FIRs involving this victim", "Generate victim impact report"],
    "ACCUSED": ["Check criminal history", "Find network connections", "Show linked FIRs"],
    "EVIDENCE": ["View evidence details", "Find linked FIR", "Generate evidence chain report"],
    "FINANCIAL": ["Analyze transaction patterns", "Find suspicious activity", "Link to case"],
    "HOTSPOT": ["Show nearby FIRs", "Get patrol recommendations", "Predict next month trend"],
    "NETWORK": ["Analyze key connections", "Find central criminals", "View full graph"],
    "PREDICTION": ["Show current statistics", "Compare with last year", "Generate preventive actions"],
    "HISTORY": ["Find repeat offenders", "Check accused history", "Generate timeline"],
    "REPORT": ["Generate executive summary", "Export as PDF", "Schedule weekly report"],
    "default": ["Show crime summary", "Find recent FIRs", "Analyze crime hotspots"],
}

DEFAULT_FOLLOWUPS = _FOLLOWUP_MAP["default"]


def _generate_suggestions(intent: str, data: dict) -> list[str]:
    """Generate context-aware suggestions based on intent and data."""
    for prefix, suggestions in _FOLLOWUP_MAP.items():
        if intent.startswith(prefix):
            return suggestions[:3]
    return DEFAULT_FOLLOWUPS[:3]


def _format_data_for_gemini(intent: str, data: dict) -> str:
    """Format structured data into a text prompt for Gemini.

    Gemini should NEVER fetch records itself — it only receives
    structured data that has already been retrieved from MySQL.
    """
    if not data:
        return "No data available."
    return json.dumps(data, indent=2, default=str)


def _build_gemini_prompt(
    intent: str,
    data: dict,
    message: str,
    history: Optional[list[dict]] = None,
    doc_text: Optional[str] = None,
) -> str:
    """Build a prompt for Gemini that includes structured data and user query.

    The prompt contains factual data from MySQL. Gemini only generates
    a natural language response from this data — it never invents facts.
    """
    parts = [
        "You are CrimeAI, an AI assistant for the Crime Intelligence Platform.",
        "You help police officers analyze crime data, identify patterns, and generate insights.",
        "",
        "IMPORTANT: The data below was retrieved from the authoritative database.",
        "Do NOT invent or fabricate any additional crime statistics, FIRs, or case details.",
        "Only use the provided data in your response.",
        "If the data is insufficient, state what is available and suggest next steps.",
        "",
    ]

    if history:
        parts.append("Recent conversation history:")
        for h in history[-6:]:
            prefix = "Officer" if h["role"] == "user" else "CrimeAI"
            parts.append(f"{prefix}: {h['message'][:300]}")
        parts.append("")

    if doc_text:
        parts.append(f"Uploaded document context:\n{doc_text[:8000]}")
        parts.append("")

    if data:
        parts.append(f"Structured data (retrieved from MySQL):\n{_format_data_for_gemini(intent, data)}")
        parts.append("")

    parts.append(f"Officer's question: \"{message}\"")
    parts.append("")
    parts.append("Provide a clear, professional response using markdown. Be concise.")

    # ── Explanation section (appended, not modifying existing prompt) ──
    if data:
        explanation = ExplanationBuilder.build(intent, data)
        parts.append("")
        parts.append("After your response, include a separate section with the title '## Why?'")
        parts.append("that briefly explains the reasoning behind your answer.")
        parts.append("Base this explanation ONLY on the structured data provided above.")
        parts.append("Do NOT invent any facts.")
        if explanation.get("evidence"):
            parts.append("Key evidence points from the data:")
            for ev in explanation["evidence"][:5]:
                parts.append(ev)

    return "\n".join(parts)


class ChatService:
    """Central orchestrator for the Hybrid SQL + LLM chat architecture.

    Flow:
        receive message
        → translate if Kannada (Gemini translation)
        → resolve pronouns using conversation context
        → classify intent (rule-based, no Gemini)
        → route to service (ServiceRouter → existing module service)
        → update conversation context with retrieved entities
        → optionally call Gemini for summarization (only on structured data)
        → translate response to Kannada if needed
        → build standardized response (ResponseBuilder)
        → persist conversation history
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._gemini = GeminiService()
        self._translator = TranslationService()
        self._repo = ChatRepository(session)
        self._demo_router = DemoRouter()

    # ── Main Entry Point ────────────────────────────────────────

    async def send_message(self, request: ChatRequest, user_id: int) -> ChatResponse:
        """Process a user message through the Hybrid SQL + LLM pipeline.

        Steps:
          1. Resolve/create conversation
          2. Save user message (original — may be Kannada)
          3. If Kannada, translate to English (Gemini translation)
          4. Resolve pronouns using conversation context
          5. Check for image attachments (→ Gemini Vision)
          6. Classify intent (rule-based, using resolved English message)
          7. Route to service for data retrieval (MySQL)
          8. Update conversation context with retrieved entities
          9. Optionally call Gemini for summarization (on structured data only)
         10. If Kannada, translate response back to Kannada
         11. Build standardized response via ResponseBuilder
         12. Save assistant response
         13. Return ChatResponse (backward compatible)
        """
        start_time = time.monotonic()
        intent_name: str = ""
        structured_data: dict[str, Any] = {}
        summary: Optional[str] = None
        suggestions: list[str] = []
        explanation_data: dict[str, Any] = {}
        is_kannada = request.language == "kn"

        # ── Step 1: Resolve conversation ────────────────────────
        conv_id_int: Optional[int] = None
        if request.conversation_id and request.conversation_id.isdigit():
            try:
                conv_id_int = int(request.conversation_id)
                await self._repo.get_conversation(conv_id_int, user_id)
            except Exception:
                conv_id_int = None

        if conv_id_int is None:
            title = request.message.strip()[:60]
            conv = await self._repo.create_conversation(user_id=user_id, title=title)
            conv_id_int = conv.id

        conversation_id = str(conv_id_int)
        logger.info("Chat request", extra={
            "user_id": user_id,
            "conversation_id": conversation_id,
            "language": request.language,
        })

        # ── Step 2: Save user message (original) ────────────────
        await self._repo.add_message(conv_id_int, "user", request.message)
        recent = await self._repo.get_recent_messages(conv_id_int, limit=10)

        # ── Step 3: Translate Kannada → English ─────────────────
        original_message = request.message
        english_message = original_message

        if is_kannada:
            try:
                english_message = await self._translator.translate_to_english(original_message)
                logger.info("Kannada→English translation applied", extra={
                    "original_len": len(original_message),
                    "translated_len": len(english_message),
                })
            except Exception as exc:
                logger.error("Translation failed (kn→en), using original", extra={"error": str(exc)})
                # Fallback: use original message. Intent classifier may still
                # classify generic intents like HELP from non-English text.

        # ── Step 4: Resolve pronouns using context ──────────────
        context: ConversationContext = get_context(conv_id_int)
        process_message = context.resolve(english_message)

        if process_message != english_message:
            logger.info("Context resolution changed message", extra={
                "before": english_message[:100],
                "after": process_message[:100],
            })

        # ── Step 5: Check for image ─────────────────────────────
        image_path = await self._get_latest_image(conv_id_int)

        if image_path:
            # Route to Gemini Vision for image analysis
            reply = await self._try_gemini_vision(
                image_path, process_message,
                fallback="I could not analyze this image."
            )
            intent_name = "vision"
            structured_data = {"image": str(image_path.name)}
        else:
            # ── Step 6: Classify intent (rule-based, no Gemini) ─
            intent_result = classify_intent(process_message)
            intent_name = intent_result.intent
            needs_summary = intent_requires_ai(intent_name)

            # ── Step 7: Route to service for data ──────────────
            if request.demo_mode:
                # Demo Mode: use hard-coded sample data (no database)
                route_result = await self._demo_router.route(intent_result, process_message)
                logger.info("DemoRouter used (demo_mode=True)")
            else:
                # Production Mode: query MySQL via ServiceRouter
                router = ServiceRouter(self._session, user_id)
                route_result = await router.route(intent_result, process_message)

            if route_result.get("success"):
                structured_data = route_result.get("data", {})

                # ── Step 8: Update conversation context ─────────
                context.update(intent_name, structured_data)
            else:
                # ── Step 11: Build standardized error response ──
                error_msg = route_result.get("error", "I could not retrieve that information.")
                builder_result = ResponseBuilder.build_error(
                    intent=intent_name,
                    error=error_msg,
                    suggestions=_generate_suggestions(intent_name, {}),
                )
                reply = error_msg
                suggestions = builder_result.get("suggestions", [])
                structured_data = builder_result.get("data", {})

                # Step 10: Translate error response if Kannada
                if is_kannada and reply:
                    try:
                        reply = await self._translator.translate_to_kannada(reply)
                    except Exception as exc:
                        logger.error("Translation failed (en→kn) for error", extra={"error": str(exc)})

                # Save and return early
                assistant_msg = await self._repo.add_message(conv_id_int, "assistant", reply)
                await self._repo.touch_conversation(conv_id_int)
                elapsed = time.monotonic() - start_time
                logger.info("Chat done", extra={
                    "elapsed_ms": round(elapsed * 1000, 1),
                    "intent": intent_name,
                    "success": False,
                })
                return ChatResponse(
                    response=reply,
                    conversation_id=conversation_id,
                    message_id=assistant_msg.id,
                    timestamp=datetime.now(UTC),
                    status="success",
                    follow_ups=suggestions,
                    success=builder_result["success"],
                    intent=intent_name,
                    data=structured_data,
                    summary=reply,
                    suggestions=suggestions,
                )

            # ── Build explanation from structured data (always) ─
            explanation_data = ExplanationBuilder.build(intent_name, structured_data)

            # ── Build timeline from structured data ─────────────
            timeline_data = InvestigationTimeline.build(structured_data, intent_name)

            # ── Build recommendations from structured data ──────
            recommendation_data = RecommendationEngine.generate(structured_data)

            # ── Step 9: Optionally call Gemini for summary ──────
            if needs_summary and structured_data:
                doc_text = await self._load_document_text(conv_id_int)
                prompt = _build_gemini_prompt(
                    intent=intent_name,
                    data=structured_data,
                    message=process_message,
                    history=recent,
                    doc_text=doc_text,
                )
                reply = await self._try_gemini(prompt, fallback=None)
                if reply:
                    summary = reply
                    builder_result = ResponseBuilder.build_summary(
                        intent=intent_name,
                        data=structured_data,
                        summary=reply,
                        suggestions=_generate_suggestions(intent_name, structured_data),
                    )
                else:
                    reply = _format_data_for_gemini(intent_name, structured_data)
                    summary = None
                    builder_result = ResponseBuilder.build_success(
                        intent=intent_name,
                        data=structured_data,
                        suggestions=_generate_suggestions(intent_name, structured_data),
                    )
            else:
                # No AI needed — format data directly
                reply = self._format_response_text(intent_name, structured_data, process_message)
                builder_result = ResponseBuilder.build_success(
                    intent=intent_name,
                    data=structured_data,
                    suggestions=_generate_suggestions(intent_name, structured_data),
                )
                # For non-AI responses, explanation still gets attached

        # ── Step 10: Translate response to Kannada if needed ─
        if is_kannada and reply:
            try:
                kannada_reply = await self._translator.translate_to_kannada(reply)
                logger.info("English→Kannada translation applied")
                reply = kannada_reply
                if summary:
                    summary = kannada_reply
            except Exception as exc:
                logger.error("Translation failed (en→kn) for response", extra={"error": str(exc)})

        # ── Step 11: Build standardized response (merged) ──────
        suggestions = _generate_suggestions(intent_name, structured_data)

        # ── Step 12: Save assistant response ────────────────────
        assistant_msg = await self._repo.add_message(conv_id_int, "assistant", reply)
        await self._repo.touch_conversation(conv_id_int)

        elapsed = time.monotonic() - start_time
        logger.info("Chat done", extra={
            "elapsed_ms": round(elapsed * 1000, 1),
            "intent": intent_name,
            "has_ai_summary": summary is not None,
            "language": request.language,
        })

        # ── Step 13: Return backward compatible ChatResponse ────
        return ChatResponse(
            response=reply,
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            timestamp=datetime.now(UTC),
            status="success",
            follow_ups=suggestions,
            success=True,
            intent=intent_name,
            data=structured_data,
            summary=summary,
            suggestions=suggestions,
            explanation=explanation_data,
            timeline=timeline_data,
            recommendations=recommendation_data,
        )

    # ── Response Formatting (No AI) ─────────────────────────────

    def _format_response_text(self, intent: str, data: dict, message: str) -> str:
        """Format structured data as readable text without AI.

        Used for non-summary intents (search, list, etc.) where
        data is simply presented to the user.
        """
        if not data:
            return "No data found matching your request."

        lines = []

        # FIR search results
        if intent == "FIR_SEARCH" and "firs" in data:
            firs = data["firs"]
            if not firs:
                return "No FIRs found matching your search."
            lines.append(f"Found **{data.get('total', len(firs))}** FIR(s):")
            for f in firs[:10]:
                lines.append(f"- **{f.get('fir_number', 'N/A')}**: {f.get('title', 'No title')}  "
                             f"*Status: {f.get('status', 'N/A')} | Priority: {f.get('priority', 'N/A')}*")

        # Victim search results
        elif intent == "VICTIM_SEARCH" and "victims" in data:
            victims = data["victims"]
            if not victims:
                return "No victims found matching your search."
            lines.append(f"Found **{data.get('total', len(victims))}** victim(s):")
            for v in victims[:10]:
                lines.append(f"- **{v.get('full_name', 'N/A')}** "
                             f"*Phone: {v.get('phone', 'N/A')} | Age: {v.get('age', 'N/A')}*")

        # Accused search results
        elif intent == "ACCUSED_SEARCH" and "accused" in data:
            accused = data["accused"]
            if not accused:
                return "No accused persons found matching your search."
            lines.append(f"Found **{data.get('total', len(accused))}** accused person(s):")
            for a in accused[:10]:
                lines.append(f"- **{a.get('full_name', 'N/A')}** "
                             f"*Risk: {a.get('risk_score', 'N/A')} | Repeat: {a.get('is_repeat_offender', False)}*")

        # Evidence results
        elif intent == "EVIDENCE_SEARCH" and "evidence" in data:
            evs = data["evidence"]
            if not evs:
                return "No evidence found matching your search."
            lines.append(f"Found **{data.get('total', len(evs))}** evidence record(s):")
            for e in evs[:10]:
                lines.append(f"- **{e.get('evidence_name', 'N/A')}** "
                             f"*Type: {e.get('evidence_type', 'N/A')} | FIR: {e.get('fir_id', 'N/A')}*")

        # Financial transactions
        elif "FINANCIAL" in intent and "transactions" in data:
            txs = data["transactions"]
            if not txs:
                return "No financial transactions found."
            lines.append(f"Found **{data.get('total', len(txs))}** transaction(s):")
            total_amount = sum(t.get("amount", 0) for t in txs)
            for t in txs[:10]:
                lines.append(f"- **{t.get('bank_name', 'N/A')}** | "
                             f"₹{t.get('amount', 0):,.2f} | {t.get('transaction_date', 'N/A')}")
            lines.append(f"\n**Total amount:** ₹{total_amount:,.2f}")

        # Hotspots
        elif "HOTSPOT" in intent and "hotspots" in data:
            hotspots = data["hotspots"]
            if not hotspots:
                return "No hotspot data available."
            lines.append("**Crime Hotspots:**")
            for h in hotspots[:10]:
                lines.append(f"- **{h.get('district', 'Unknown')}**: {h.get('crime_count', 0)} crimes "
                             f"*Risk: {h.get('risk_level', 'N/A')} ({h.get('risk_score', 0)})*")

        # Network
        elif "NETWORK" in intent and "nodes" in data:
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            lines.append(f"**Criminal Network:** {len(nodes)} nodes, {len(edges)} connections")
            for n in nodes[:10]:
                lines.append(f"- **{n.get('label', 'Unknown')}** ({n.get('type', 'Unknown')})")

        # Help
        elif intent == "HELP":
            caps = data.get("capabilities", [])
            examples = data.get("examples", [])
            lines.append("**I can help you with:**")
            for c in caps:
                lines.append(f"- {c}")
            lines.append("")
            lines.append("**Try asking:**")
            for ex in examples:
                lines.append(f"- \"{ex}\"")

        # Settings
        elif intent == "SETTINGS":
            lines.append(f"Your settings are loaded. Use the Settings module to update preferences.")

        # Default: format data as readable JSON
        else:
            formatted = json.dumps(data, indent=2, default=str)[:1000]
            lines.append(f"```json\n{formatted}\n```")

        return "\n\n".join(lines)

    # ── Gemini Integration ──────────────────────────────────────
    # Gemini is ONLY called for summarization/reasoning on
    # structured data that was already retrieved from MySQL.

    async def _try_gemini(self, prompt: str, fallback: Optional[str] = None) -> Optional[str]:
        """Call Gemini for summarization. Never for data retrieval.

        Returns the AI-generated text, or the fallback (which may be None
        to indicate the caller should use a non-AI fallback).
        """
        try:
            return await self._gemini.generate_response(prompt)
        except RuntimeError as exc:
            logger.warning("Gemini fallback", extra={"error": str(exc)})
            return fallback
        except Exception as exc:
            logger.error("Gemini unexpected error", extra={"error": str(exc)})
            return fallback

    async def _try_gemini_vision(self, image_path: Path, question: str,
                                  fallback: str = "I could not analyze this image.") -> str:
        """Call Gemini Vision for image analysis."""
        try:
            return await self._gemini.analyze_image(image_path, question)
        except RuntimeError as exc:
            logger.warning("Gemini Vision fallback", extra={"error": str(exc)})
            return fallback
        except Exception as exc:
            logger.error("Gemini Vision unexpected error", extra={"error": str(exc)})
            return fallback

    # ── Image & Document Helpers ────────────────────────────────

    async def _get_latest_image(self, conv_id: int) -> Optional[Path]:
        """Get the most recent image attachment for a conversation."""
        q = select(ChatAttachment).where(
            ChatAttachment.conversation_id == conv_id,
            ChatAttachment.mime_type.in_(["image/png", "image/jpeg"]),
        ).order_by(ChatAttachment.created_at.desc()).limit(1)
        r = await self._session.execute(q)
        att = r.scalar_one_or_none()
        if att:
            p = settings.CHAT_UPLOAD_DIR / att.stored_filename
            return p if p.exists() else None
        return None

    async def _load_document_text(self, conv_id: int, max_chars: int = 30000) -> Optional[str]:
        """Load concatenated extracted text from all document attachments."""
        q = select(ChatAttachment).where(
            ChatAttachment.conversation_id == conv_id,
            ChatAttachment.extracted_text.isnot(None),
            ChatAttachment.mime_type.notin_(["image/png", "image/jpeg"]),
        ).order_by(ChatAttachment.created_at.asc())
        r = await self._session.execute(q)
        attachments = r.scalars().all()
        texts = []
        total = 0
        for att in attachments:
            if att.extracted_text and not att.extracted_text.startswith("["):
                texts.append(att.extracted_text[:10000])
                total += len(att.extracted_text)
                if total >= max_chars:
                    break
        if not texts:
            return None
        return "\n---\n".join(texts)[:max_chars]
