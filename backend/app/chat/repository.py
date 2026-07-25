"""Repository layer for chat conversation persistence."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import ChatConversation, ChatMessage
from app.exceptions.handlers import ForbiddenException, NotFoundException
from app.logging import get_logger

logger = get_logger(__name__)


class ChatRepository:
    """Database operations for chat conversations and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Conversations ───────────────────────────────────────────

    async def create_conversation(self, user_id: int, title: str = "New Chat") -> ChatConversation:
        """Create a new conversation for a user."""
        conv = ChatConversation(user_id=user_id, title=title)
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        logger.info("Conversation %s created for user %s", conv.id, user_id)
        return conv

    async def get_conversation(self, conversation_id: int, user_id: int) -> ChatConversation:
        """Get a conversation by ID, ensuring the user owns it."""
        conv = await self.session.get(ChatConversation, conversation_id)
        if not conv:
            raise NotFoundException(message="Conversation not found")
        if conv.user_id != user_id:
            raise ForbiddenException(message="You do not have access to this conversation")
        return conv

    async def list_conversations(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[list[ChatConversation], int]:
        """List conversations for a user, ordered by most recent."""
        base = select(ChatConversation).where(
            ChatConversation.user_id == user_id
        ).order_by(ChatConversation.updated_at.desc())

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        q = base.offset(offset).limit(limit)
        r = await self.session.execute(q)
        items = list(r.scalars().all())
        return items, total

    async def update_title(self, conversation_id: int, title: str) -> None:
        """Update the title of a conversation."""
        conv = await self.session.get(ChatConversation, conversation_id)
        if conv:
            conv.title = title
            await self.session.flush()

    async def touch_conversation(self, conversation_id: int) -> None:
        """Update the updated_at timestamp."""
        conv = await self.session.get(ChatConversation, conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """Delete a conversation and all its messages (cascade)."""
        conv = await self.get_conversation(conversation_id, user_id)
        await self.session.delete(conv)
        await self.session.flush()
        logger.info("Conversation %s deleted by user %s", conversation_id, user_id)

    # ── Messages ────────────────────────────────────────────────

    async def add_message(
        self, conversation_id: int, role: str, message: str
    ) -> ChatMessage:
        """Append a message to a conversation."""
        msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            message=message,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_recent_messages(
        self, conversation_id: int, limit: int = 10
    ) -> list[dict[str, str]]:
        """Return the last N messages as a list of {role, message} dicts.

        Used to provide conversation context to the LLM.
        """
        q = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit)
        r = await self.session.execute(q)
        msgs = list(reversed(r.scalars().all()))
        return [{"role": m.role, "message": m.message} for m in msgs]

    async def get_message_count(self, conversation_id: int) -> int:
        """Count messages in a conversation."""
        q = select(func.count()).where(
            ChatMessage.conversation_id == conversation_id
        ).select_from(ChatMessage)
        r = await self.session.execute(q)
        return r.scalar_one()
