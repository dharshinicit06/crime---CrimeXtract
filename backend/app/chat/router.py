"""Chat API router — message, history, upload, feedback, search."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.history_router import router as history_router
from app.chat.history_schemas import ConversationSummary, ConversationListResponse
from app.chat.models import ChatConversation, ChatMessage
from app.chat.schemas import (
    ChatRequest, ChatResponse, ChatResponse as CR,
    FeedbackRequest, FeedbackResponse,
)
from app.chat.services import ChatService
from app.chat.upload_router import router as upload_router
from app.chat.repository import ChatRepository
from app.dependencies import get_current_user, get_db_session
from app.logging import get_logger
from app.chat.pdf_export import generate_conversation_pdf
# Rate limiter temporarily disabled due to slowapi compatibility
from app.chat.speech_service import SpeechService
from app.rate_limit import upload_limiter

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
router.include_router(history_router)
router.include_router(upload_router)


# ── Speech endpoints ────────────────────────────────────────────

_speech_service = SpeechService()


@router.post("/speech-to-text", summary="Transcribe audio to text")
async def speech_to_text_endpoint(
    file: bytes = File(...),
    filename: str = "audio.webm",
    language: str = "en",
    current_user: User = Depends(get_current_user),
):
    """Upload an audio file and receive transcribed text.

    Supports English (en) and Kannada (kn).
    Accepts multipart upload with field name 'file'.
    Returns JSON with the transcribed text.
    """
    try:
        text = await _speech_service.speech_to_text(
            audio_data=file, filename=filename, language=language,
        )
        return {"text": text, "language": language}
    except Exception as exc:
        logger.error("STT endpoint failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail="Speech recognition failed")


@router.post("/text-to-speech", summary="Convert text to speech audio")
async def text_to_speech_endpoint(
    text: str,
    language: str = "en",
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech audio.

    Supports English (en) and Kannada (kn).
    Returns MP3 audio bytes.
    """
    from fastapi.responses import Response
    try:
        audio_bytes = await _speech_service.text_to_speech(
            text=text, language=language,
        )
        if audio_bytes is None:
            raise HTTPException(status_code=503, detail="Text-to-speech service unavailable")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'inline; filename="speech.mp3"',
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("TTS endpoint failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail="Text-to-speech failed")


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    return ChatService(session=session)


@router.post("/message", response_model=CR, summary="Send a message")
# @chat_limiter  # Uncomment when slowapi compatibility is resolved
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        return await service.send_message(request=request, user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat failed", extra={"error": str(exc), "user_id": current_user.id})
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.get(
    "/{conversation_id}/export-pdf",
    summary="Export conversation as PDF",
    responses={
        200: {
            "description": "PDF file download",
            "content": {"application/pdf": {}},
        },
        403: {"description": "Access denied"},
        404: {"description": "Conversation not found"},
    },
)
async def export_conversation_pdf(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Export a chat conversation as a professional PDF document.

    Retrieves the conversation with all messages, generates a PDF
    with ReportLab, and returns it as a downloadable file.
    """
    from fastapi.responses import StreamingResponse

    # Fetch conversation with messages using existing repository
    repo = ChatRepository(session)
    conv = await repo.get_conversation(conversation_id, user_id=current_user.id)

    # Build messages list in the format expected by pdf_export
    messages_data = []
    for m in conv.messages:
        messages_data.append({
            "role": m.role,
            "message": m.message,
            "created_at": m.created_at,
        })

    # Look up officer role name from roles table
    from app.auth.role_models import Role
    officer_role = "Officer"
    if current_user.role_id:
        role_q = select(Role.role_name).where(Role.role_id == current_user.role_id)
        role_r = await session.execute(role_q)
        role_name = role_r.scalar_one_or_none()
        if role_name:
            officer_role = role_name

    # Generate PDF
    pdf_buf = generate_conversation_pdf(
        conversation_id=conversation_id,
        title=conv.title,
        messages=messages_data,
        officer_name=current_user.full_name or "Officer",
        officer_role=officer_role,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )

    filename = f"crimeai-conversation-{conversation_id}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        },
    )


@router.post("/feedback", response_model=FeedbackResponse, summary="Submit message feedback")
async def submit_feedback(
    fb: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FeedbackResponse:
    """Record thumbs up/down feedback for a specific message.

    If message_id is not provided (0 or None), automatically resolves
    to the last assistant message in the conversation.
    """
    from app.chat.models import ChatMessage as CM
    from sqlalchemy import select

    message_id = fb.message_id

    # Auto-resolve message_id if not provided
    if not message_id or message_id == 0:
        q = select(CM.id).where(
            CM.conversation_id == fb.conversation_id,
            CM.role == "assistant",
        ).order_by(CM.created_at.desc()).limit(1)
        r = await session.execute(q)
        row = r.one_or_none()
        if row:
            message_id = row[0]

    msg = await session.get(CM, message_id) if message_id else None
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    conv = await session.get(ChatConversation, fb.conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    logger.info("Feedback recorded", extra={
        "message_id": message_id, "rating": fb.rating,
        "conversation_id": fb.conversation_id, "user_id": current_user.id,
    })
    return FeedbackResponse(success=True, message="Feedback recorded")


@router.get("/conversations/search", response_model=ConversationListResponse,
            summary="Search conversations by title or content")
async def search_conversations(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationListResponse:
    """Search conversations by title or message content."""
    pattern = f"%{q}%"
    # Find conversations matching title
    title_q = select(ChatConversation).where(
        ChatConversation.user_id == current_user.id,
        ChatConversation.title.ilike(pattern),
    ).order_by(ChatConversation.updated_at.desc()).limit(50)
    r = await session.execute(title_q)
    by_title = {c.id: c for c in r.scalars().all()}

    # Find conversations whose messages contain the query
    msg_q = select(ChatMessage.conversation_id).where(
        ChatMessage.message.ilike(pattern)
    ).distinct().limit(50)
    r = await session.execute(msg_q)
    matched_ids = [row[0] for row in r.all()]
    if matched_ids:
        conv_q = select(ChatConversation).where(
            ChatConversation.id.in_(matched_ids),
            ChatConversation.user_id == current_user.id,
        ).order_by(ChatConversation.updated_at.desc()).limit(50)
        r = await session.execute(conv_q)
        for c in r.scalars().all():
            by_title[c.id] = c

    items = list(by_title.values())
    items.sort(key=lambda c: c.updated_at or c.created_at, reverse=True)
    items = items[:50]

    summaries = []
    for c in items:
        count_q = select(ChatMessage).where(ChatMessage.conversation_id == c.id)
        cr = await session.execute(count_q)
        cnt = len(list(cr.scalars().all()))
        summaries.append(ConversationSummary(
            id=c.id, title=c.title, user_id=c.user_id,
            message_count=cnt, created_at=c.created_at, updated_at=c.updated_at,
        ))
    return ConversationListResponse(items=summaries, total=len(summaries))
