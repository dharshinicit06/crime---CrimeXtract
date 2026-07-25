"""ConversationHistory ORM model matching the existing MySQL conversation_history table."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Index, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    __table_args__ = (
        Index("idx_conversation_user", "user_id"),
    )

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_response: Mapped[str | None] = mapped_column(
        LONGTEXT,
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationHistory("
            f"conversation_id={self.conversation_id}, "
            f"user_id={self.user_id})>"
        )
