"""Pydantic schemas for conversation history CRUD."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    """A single chat message in history."""
    id: int
    role: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    id: int
    title: str
    user_id: int
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: int
    title: str
    user_id: int
    messages: list[MessageSchema] = []
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Paginated conversation list."""
    items: list[ConversationSummary]
    total: int


class DeleteResult(BaseModel):
    """Result of a delete operation."""
    success: bool = True
    message: str = "Conversation deleted"
