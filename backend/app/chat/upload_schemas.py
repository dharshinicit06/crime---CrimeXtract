"""Pydantic schemas for file upload."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response after a successful file upload."""
    file_id: int = Field(..., description="Database ID of the attachment")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="File size in bytes")
    conversation_id: int = Field(..., description="Conversation the file belongs to")
    message: str = Field(default="File uploaded successfully", description="Status message")


class UploadError(BaseModel):
    """Upload error response."""
    detail: str = Field(..., description="Error description")
