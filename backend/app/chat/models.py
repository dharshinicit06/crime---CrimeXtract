"""SQLAlchemy models for chat conversation history and attachments."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="conversation",
        cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )
    attachments: Mapped[list["ChatAttachment"]] = relationship(
        "ChatAttachment", back_populates="conversation",
        cascade="all, delete-orphan", order_by="ChatAttachment.created_at"
    )

    def __repr__(self) -> str:
        return f"<ChatConversation {self.id}: {self.title}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'user' or 'assistant'"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["ChatConversation"] = relationship(
        "ChatConversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id}: {self.role}>"


class ChatAttachment(Base):
    """An uploaded file attached to a chat conversation."""

    __tablename__ = "chat_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["ChatConversation"] = relationship(
        "ChatConversation", back_populates="attachments"
    )

    def __repr__(self) -> str:
        return f"<ChatAttachment {self.id}: {self.filename}>"
