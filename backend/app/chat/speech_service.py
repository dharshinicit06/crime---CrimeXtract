"""Speech Service — Speech-to-Text and Text-to-Speech using Gemini + gTTS.

This module provides voice support for the Crime Intelligence Platform.
It uses Google's generativeai API (same as GeminiService) for transcription
and gTTS for speech synthesis.

No existing APIs are modified. This is a standalone service.

Supported languages:
  - English (en)
  - Kannada (kn)
"""

import io
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class SpeechService:
    """Speech-to-Text and Text-to-Speech using Gemini + gTTS."""

    def __init__(self) -> None:
        self._api_key = settings.GEMINI_API_KEY

    # ── Speech-to-Text ──────────────────────────────────────────

    async def speech_to_text(
        self, audio_data: bytes, filename: str = "audio.webm",
        language: str = "en",
    ) -> str:
        """Transcribe audio to text using Gemini.

        Uses the same google.generativeai library as GeminiService.
        Uploads the audio file, then sends it with a transcription prompt.

        Args:
            audio_data: Raw audio bytes (e.g. WebM from browser recording).
            filename: Original filename (used to infer mime type).
            language: Expected language ("en" or "kn").

        Returns:
            Transcribed text string, or "" on failure.
        """
        if not self._api_key or self._api_key in ("", "your-gemini-api-key-here"):
            logger.warning("Gemini API key not configured — STT unavailable")
            return ""

        try:
            genai.configure(api_key=self._api_key)

            # Save audio to a temp file for upload
            suffix = Path(filename).suffix if Path(filename).suffix else ".webm"
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = Path(tmp.name)

            mime_type = self._infer_mime(filename)
            lang_hint = "Kannada" if language == "kn" else "English"

            prompt = (
                f"Transcribe the following audio to text. "
                f"The audio is in {lang_hint}. "
                f"Return ONLY the transcribed text, nothing else. "
                f"Keep all numbers, names, and identifiers exactly as spoken."
            )

            # Upload file and generate content with the audio
            uploaded_file = genai.upload_file(str(tmp_path), mime_type=mime_type)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, uploaded_file])

            # Clean up temp file and uploaded file
            try:
                tmp_path.unlink()
                genai.delete_file(uploaded_file.name)
            except Exception:
                pass

            text = response.text.strip() if response and response.text else ""
            if not text:
                logger.warning("Gemini returned empty transcription")
                return ""

            logger.info("STT transcription successful", extra={
                "text_len": len(text), "language": language,
            })
            return text

        except Exception as exc:
            logger.error("STT failed", extra={"error": str(exc), "language": language})
            return ""

    # ── Text-to-Speech ──────────────────────────────────────────

    async def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Convert text to speech audio using gTTS.

        Args:
            text: Text to synthesize.
            language: Language code ("en" or "kn").

        Returns:
            MP3 audio bytes, or None on failure.
        """
        try:
            import gtts
            lang_map = {"en": "en", "kn": "kn"}
            tts_lang = lang_map.get(language, "en")

            tts = gtts.gTTS(text=text, lang=tts_lang, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            audio_bytes = buf.read()

            logger.info("TTS synthesis successful", extra={
                "text_len": len(text), "language": language,
                "audio_size": len(audio_bytes),
            })
            return audio_bytes

        except ImportError:
            logger.warning("gTTS not installed. TTS unavailable.")
            return None
        except Exception as exc:
            logger.error("TTS failed", extra={"error": str(exc), "language": language})
            return None

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _infer_mime(filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        mime_map = {
            ".webm": "audio/webm", ".wav": "audio/wav",
            ".mp3": "audio/mpeg", ".ogg": "audio/ogg",
            ".m4a": "audio/mp4", ".mp4": "audio/mp4",
            ".flac": "audio/flac",
        }
        return mime_map.get(suffix, "audio/webm")
