"""Document text extraction service for uploaded files."""

from pathlib import Path
from typing import Optional

from app.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz
    doc = fitz.open(str(file_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    text = "\n\n".join(pages).strip()
    logger.debug("Extracted %d chars from PDF %s", len(text), Path(file_path).name)
    return text or "[No extractable text found in PDF]"


def extract_text_from_docx(file_path: str | Path) -> str:
    """Extract text from a DOCX using python-docx."""
    from docx import Document
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    logger.debug("Extracted %d chars from DOCX %s", len(text), Path(file_path).name)
    return text or "[No extractable text found in DOCX]"


def extract_text_from_txt(file_path: str | Path) -> str:
    """Read text from a plain text file."""
    path = Path(file_path)
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    logger.debug("Read %d chars from TXT %s", len(text), path.name)
    return text or "[Empty text file]"


def extract_text(file_path: str | Path, mime_type: str) -> str:
    """Route to the correct extractor based on MIME type."""
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif mime_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
        return extract_text_from_docx(file_path)
    elif mime_type == "text/plain":
        return extract_text_from_txt(file_path)
    else:
        return ""  # Images return empty — handled by Gemini Vision


def is_image_mime(mime_type: str) -> bool:
    """Check if the MIME type corresponds to an image."""
    return mime_type.startswith("image/")
