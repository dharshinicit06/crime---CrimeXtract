"""Conversation history API endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.history_schemas import (
    ConversationDetail,
    ConversationListResponse,
    ConversationSummary,
    DeleteResult,
)
from app.chat.repository import ChatRepository
from app.dependencies import get_current_user, get_db_session
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=["Chat-History"],
)


def get_repo(session: AsyncSession = Depends(get_db_session)) -> ChatRepository:
    return ChatRepository(session=session)


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List user's chat conversations",
)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    repo: ChatRepository = Depends(get_repo),
) -> ConversationListResponse:
    """List all conversations for the authenticated user, newest first."""
    items, total = await repo.list_conversations(
        user_id=current_user.id, limit=limit, offset=offset
    )
    summaries = []
    for c in items:
        count = await repo.get_message_count(c.id)
        summaries.append(ConversationSummary(
            id=c.id,
            title=c.title,
            user_id=c.user_id,
            message_count=count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ))
    return ConversationListResponse(items=summaries, total=total)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get a conversation with all messages",
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    repo: ChatRepository = Depends(get_repo),
) -> ConversationDetail:
    """Get a single conversation with its messages."""
    conv = await repo.get_conversation(conversation_id, user_id=current_user.id)
    count = await repo.get_message_count(conv.id)
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        user_id=conv.user_id,
        messages=[
            {"id": m.id, "role": m.role, "message": m.message, "created_at": m.created_at}
            for m in conv.messages
        ],
        message_count=count,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteResult,
    summary="Delete a conversation",
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    repo: ChatRepository = Depends(get_repo),
) -> DeleteResult:
    """Delete a conversation and all its messages."""
    await repo.delete_conversation(conversation_id, user_id=current_user.id)
    return DeleteResult(success=True, message="Conversation deleted")
