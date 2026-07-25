"""Pydantic schemas for Chat API — Hybrid SQL + LLM architecture.

Defines request/response formats for all chat endpoints.
The standardized response format includes:
  - success: bool
  - intent: str
  - data: dict
  - summary: Optional[str]
  - suggestions: list[str]
  - conversation_id: int
"""

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the user.

    Supports:
      - ``language``: "en" (English) or "kn" (Kannada)
        When "kn", the message is translated to English before intent
        classification, and the response is translated back to Kannada.
      - ``demo_mode``: When True, routes through DemoService instead
        of querying production MySQL.
    """
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None)
    language: str = Field(default="en", pattern="^(en|kn)$")
    demo_mode: bool = Field(default=False, description="Use DemoService instead of production databases")


class ChatResponse(BaseModel):
    """Standardized chat response with structured data and optional AI summary.

    Backward compatible — retains the original ``response`` field for
    existing frontend clients. New fields (success, intent, data, etc.)
    provide the structured Hybrid SQL + LLM format.
    """
    # ── Backward compatible fields ───────────────────────────────
    response: str = Field(..., description="The assistant's reply (markdown)")
    conversation_id: str = Field(...)
    message_id: Optional[int] = Field(None, description="The ID of the assistant message for feedback")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field(default="success")
    follow_ups: list[str] = Field(default_factory=list, description="Suggested follow-up questions")

    # ── Hybrid SQL + LLM structured fields ──────────────────────
    success: bool = Field(default=True, description="Request success indicator")
    intent: str = Field(default="", description="Classified intent name")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured data from MySQL (no AI)")
    summary: Optional[str] = Field(None, description="AI-generated natural language summary")
    suggestions: list[str] = Field(default_factory=list, description="Suggested next actions")

    # ── Explainable AI ───────────────────────────────────────────
    explanation: dict[str, Any] = Field(
        default_factory=dict,
        description="Evidence-based explanation with keys: answer, explanation, evidence",
    )

    # ── Investigation Timeline ────────────────────────────────────
    timeline: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological investigation timeline events",
    )

    # ── Smart Recommendations ─────────────────────────────────────
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Investigation recommendations with icons, actions, reasons, and priorities",
    )


class FeedbackRequest(BaseModel):
    """User feedback on a chat message."""
    conversation_id: int = Field(...)
    message_id: Optional[int] = Field(None, description="Message ID (auto-resolved if not provided)")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Feedback submission result."""
    success: bool = True
    message: str = "Feedback recorded"


class MessageResponse(BaseModel):
    """A single chat message in a conversation."""
    id: int
    role: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """A conversation with all its messages."""
    id: int
    title: str
    user_id: int
    messages: list[MessageResponse] = []
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
