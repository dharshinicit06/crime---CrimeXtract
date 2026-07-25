"""Gemini AI service — text generation and Vision support for CrimeAI."""

import logging
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are CrimeAI, an AI-powered assistant for the Crime Intelligence Platform. "
    "You assist police officers, crime analysts, and investigators with crime data analysis, "
    "pattern recognition, and intelligence gathering. "
    "Answer professionally and concisely. "
    "Do not invent facts or crime statistics. "
    "If information is unavailable or outside your knowledge, clearly state that. "
    "Be concise, investigative, and helpful. "
    "Always maintain a professional and security-conscious tone."
)

_api_key: Optional[str] = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None
_model = None

if _api_key and _api_key not in ("", "your-gemini-api-key-here"):
    try:
        genai.configure(api_key=_api_key)
        _model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        logger.info("Gemini model configured", extra={"model": "gemini-1.5-flash"})
    except Exception as exc:
        _model = None
        logger.error("Failed to configure Gemini model", extra={"error": str(exc)})
else:
    logger.warning("GEMINI_API_KEY not set — Gemini integration disabled")


class GeminiService:
    """Service that interacts with the Google Gemini API.

    Supports both text-only and multimodal (image + text) requests.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable,
             google_exceptions.DeadlineExceeded, google_exceptions.InternalServerError)
        ),
        before_sleep=before_sleep_log(logger, log_level=logging.WARNING),
    )
    async def generate_response(self, message: str) -> str:
        """Text-only generation."""
        if _model is None:
            raise RuntimeError("Gemini AI is not configured. Set GEMINI_API_KEY.")
        if not message or not message.strip():
            return "I received your request but could not generate a meaningful response."
        logger.debug("Sending text to Gemini", extra={"message_length": len(message)})
        start_time = time.monotonic()
        try:
            response = await _model.generate_content_async(message)
            elapsed = time.monotonic() - start_time
            logger.info("Gemini response received", extra={"response_time_ms": round(elapsed * 1000, 1), "response_length": len(response.text) if response.text else 0})
            if not response.text:
                return "I received your request but could not generate a meaningful response. Please try rephrasing."
            return response.text.strip()
        except google_exceptions.Unauthenticated:
            logger.error("Gemini authentication failed — invalid API key")
            raise RuntimeError("AI assistant authentication failed. Please contact the administrator.")
        except google_exceptions.PermissionDenied as exc:
            logger.error("Gemini permission denied", extra={"error": str(exc)})
            raise RuntimeError("AI assistant access denied. Please contact the administrator.")
        except google_exceptions.ResourceExhausted as exc:
            logger.warning("Gemini rate limit exceeded", extra={"error": str(exc)})
            raise RuntimeError("AI assistant is temporarily busy. Please try again shortly.")
        except google_exceptions.ServiceUnavailable as exc:
            logger.warning("Gemini service unavailable", extra={"error": str(exc)})
            raise RuntimeError("AI assistant is temporarily unavailable. Please try again later.")
        except google_exceptions.GoogleAPICallError as exc:
            logger.error("Gemini API call failed", extra={"error": str(exc), "status_code": getattr(exc, "code", None)})
            raise RuntimeError("AI assistant encountered an error. Please try again later.")
        except Exception as exc:
            logger.error("Unexpected Gemini error", extra={"error": str(exc), "type": type(exc).__name__})
            raise RuntimeError("AI assistant is temporarily unavailable.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable,
             google_exceptions.DeadlineExceeded, google_exceptions.InternalServerError)
        ),
        before_sleep=before_sleep_log(logger, log_level=logging.WARNING),
    )
    async def analyze_image(self, image_path: str | Path, question: str = "Describe this image in detail") -> str:
        """Analyze an image using Gemini Vision.

        Args:
            image_path: Path to the image file (PNG, JPG, JPEG).
            question: The user's question about the image.

        Returns:
            Gemini's analysis of the image.
        """
        if _model is None:
            raise RuntimeError("Gemini AI is not configured. Set GEMINI_API_KEY.")

        try:
            import PIL.Image
            img = PIL.Image.open(str(image_path))
        except Exception as exc:
            logger.error("Failed to open image", extra={"path": str(image_path), "error": str(exc)})
            raise RuntimeError("Failed to process the image file.")

        logger.debug("Sending image to Gemini Vision", extra={"path": str(image_path)})
        start_time = time.monotonic()
        try:
            response = await _model.generate_content_async([question, img])
            elapsed = time.monotonic() - start_time
            logger.info("Gemini Vision response received", extra={"response_time_ms": round(elapsed * 1000, 1)})
            img.close()
            if not response.text:
                return "I could not analyze this image. Please try a different image or question."
            return response.text.strip()
        except google_exceptions.GoogleAPICallError as exc:
            img.close()
            logger.error("Gemini Vision failed", extra={"error": str(exc)})
            raise RuntimeError("AI assistant could not analyze the image. Please try again.")
        except Exception as exc:
            img.close()
            logger.error("Unexpected Gemini Vision error", extra={"error": str(exc)})
            raise RuntimeError("AI assistant is temporarily unavailable.")
