"""File upload endpoint for the CrimeAI chat."""

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.document_service import extract_text, is_image_mime
from app.chat.models import ChatAttachment
from app.chat.repository import ChatRepository
from app.chat.upload_schemas import UploadResponse
from app.config import settings
from app.dependencies import get_current_user, get_db_session
from app.logging import get_logger
from app.rate_limit import upload_limiter

logger = get_logger(__name__)

router = APIRouter(
    tags=["Chat-Upload"],
)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/png",
    "image/jpeg",
}

MAX_FILE_SIZE = settings.CHAT_UPLOAD_MAX_SIZE
UPLOAD_DIR = settings.CHAT_UPLOAD_DIR


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file to a chat conversation",
)
@upload_limiter
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: int = Form(0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UploadResponse:
    """Upload a PDF, DOCX, TXT, PNG, or JPG file to a chat conversation."""

    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    content_type = file.content_type or "application/octet-stream"

    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX, TXT, PNG, JPG.",
        )

    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    repo = ChatRepository(session)

    if conversation_id and conversation_id > 0:
        conv = await repo.get_conversation(
            conversation_id,
            user_id=current_user.id,
        )

        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        conv = await repo.create_conversation(
            user_id=current_user.id,
            title=f"Document: {file.filename}",
        )

    ext = Path(file.filename).suffix
    stored_name = f"{uuid.uuid4().hex}{ext}"

    upload_path = UPLOAD_DIR / stored_name
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    upload_path.write_bytes(contents)

    extracted_text = None

    if not is_image_mime(content_type):
        try:
            extracted_text = extract_text(upload_path, content_type)
        except Exception as exc:
            logger.warning(
                "Text extraction failed",
                extra={
                    "file": file.filename,
                    "error": str(exc),
                },
            )
            extracted_text = "[Text extraction failed]"

    attachment = ChatAttachment(
        conversation_id=conv.id,
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=stored_name,
        mime_type=content_type,
        file_size=file_size,
        extracted_text=extracted_text,
    )

    session.add(attachment)
    await session.flush()
    await session.refresh(attachment)

    logger.info(
        "File uploaded",
        extra={
            "file_id": attachment.id,
            "filename": file.filename,
            "size": file_size,
            "mime": content_type,
            "conversation_id": conv.id,
            "user_id": current_user.id,
        },
    )

    return UploadResponse(
        file_id=attachment.id,
        filename=file.filename,
        mime_type=content_type,
        file_size=file_size,
        conversation_id=conv.id,
        message=f"File '{file.filename}' uploaded successfully",
    )