"""Gemini Translation Helper — Kannada ↔ English translation for CrimeAI.

Uses Gemini exclusively for translation. No external translation APIs.
Translations preserve all FIR numbers, dates, IDs, locations, names, IPC
sections, and other technical police terminology unchanged.
"""

import logging
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

# ─── Translation Prompts ─────────────────────────────────────────

KANNADA_TO_ENGLISH_PROMPT = (
    "You are a professional translator for the Karnataka Police Department.\n"
    "Translate the following Kannada police query into English.\n"
    "Keep all FIR numbers, dates, IDs, locations and names unchanged.\n"
    "Return only the translated sentence.\n"
    "---\n"
)

ENGLISH_TO_KANNADA_PROMPT = (
    "You are a professional translator for the Karnataka Police Department.\n"
    "Translate the following response into professional Kannada.\n"
    "Rules:\n"
    "- Do NOT translate: FIR, Crime ID, GPS, AI, IPC Sections, Bank Names,\n"
    "  Officer Names, Dates, Case Numbers\n"
    "- Keep technical police terminology accurate.\n"
    "- Return only the translated sentence.\n"
    "---\n"
)

# ─── Gemini Model Setup ─────────────────────────────────────────

_api_key: Optional[str] = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None
_translation_model = None

if _api_key and _api_key not in ("", "your-gemini-api-key-here"):
    try:
        genai.configure(api_key=_api_key)
        _translation_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
        )
        logger.info("Translation Gemini model configured")
    except Exception as exc:
        _translation_model = None
        logger.error("Failed to configure translation model", extra={"error": str(exc)})
else:
    logger.warning("GEMINI_API_KEY not set — translation disabled")


class TranslationService:
    """Kannada ↔ English translation using Gemini.

    Uses a separate Gemini model instance (no system prompt) to perform
    clean translations without the CrimeAI persona affecting output.
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
    async def translate_to_english(self, text: str) -> str:
        """Translate Kannada text to English using Gemini."""
        if _translation_model is None:
            logger.warning("Translation model not available — returning original text")
            return text
        if not text or not text.strip():
            return text
        prompt = KANNADA_TO_ENGLISH_PROMPT + text
        logger.debug("Translating Kannada → English", extra={"text_length": len(text)})
        try:
            response = await _translation_model.generate_content_async(prompt)
            translated = response.text.strip() if response.text else text
            logger.info("Translation complete (kn→en)", extra={
                "input_length": len(text), "output_length": len(translated),
            })
            return translated
        except google_exceptions.GoogleAPICallError as exc:
            logger.error("Translation API error (kn→en)", extra={"error": str(exc)})
            return text
        except Exception as exc:
            logger.error("Unexpected translation error (kn→en)", extra={"error": str(exc)})
            return text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable,
             google_exceptions.DeadlineExceeded, google_exceptions.InternalServerError)
        ),
        before_sleep=before_sleep_log(logger, log_level=logging.WARNING),
    )
    async def translate_to_kannada(self, text: str) -> str:
        """Translate English text to professional Kannada using Gemini."""
        if _translation_model is None:
            logger.warning("Translation model not available — returning original text")
            return text
        if not text or not text.strip():
            return text
        prompt = ENGLISH_TO_KANNADA_PROMPT + text
        logger.debug("Translating English → Kannada", extra={"text_length": len(text)})
        try:
            response = await _translation_model.generate_content_async(prompt)
            translated = response.text.strip() if response.text else text
            logger.info("Translation complete (en→kn)", extra={
                "input_length": len(text), "output_length": len(translated),
            })
            return translated
        except google_exceptions.GoogleAPICallError as exc:
            logger.error("Translation API error (en→kn)", extra={"error": str(exc)})
            return text
        except Exception as exc:
            logger.error("Unexpected translation error (en→kn)", extra={"error": str(exc)})
            return text
