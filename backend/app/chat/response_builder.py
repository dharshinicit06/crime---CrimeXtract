"""Response Builder — standardized chat response format.

Every module returns the same format through this builder.
Ensures the frontend always receives a consistent structure.

Version: 2.0 (Hybrid SQL + LLM)
"""

from typing import Any, Optional


class ResponseBuilder:
    """Creates standardized API responses for the chat system.

    Every response follows the same shape:
    {
        "success": bool,
        "intent": str,
        "data": dict,
        "summary": Optional[str],
        "suggestions": list[str],
    }
    """

    @staticmethod
    def build_success(
        intent: str,
        data: dict[str, Any],
        summary: Optional[str] = None,
        suggestions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Build a success response with structured data.

        Args:
            intent: The classified intent name.
            data: Structured data from the module service (no AI).
            summary: Optional AI-generated natural language summary.
            suggestions: Optional list of suggested next actions.

        Returns:
            Standardized response dict.
        """
        return {
            "success": True,
            "intent": intent,
            "data": data if data else {},
            "summary": summary,
            "suggestions": suggestions or [],
        }

    @staticmethod
    def build_error(
        intent: str,
        error: str,
        data: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Build an error response.

        Args:
            intent: The classified intent name.
            error: Human-readable error description.
            data: Optional partial data that was retrieved before the error.
            suggestions: Optional list of suggested next actions.

        Returns:
            Standardized error response dict.
        """
        return {
            "success": False,
            "intent": intent,
            "data": data if data else {},
            "summary": error,
            "suggestions": suggestions or [],
        }

    @staticmethod
    def build_summary(
        intent: str,
        data: dict[str, Any],
        summary: str,
        suggestions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Build a response where the AI summary is the primary output.

        Used for summary intents where the LLM generates
        the main response text from structured data.

        Args:
            intent: The classified intent name.
            data: The structured data used to generate the summary.
            summary: The AI-generated natural language summary.
            suggestions: Optional list of suggested next actions.

        Returns:
            Standardized summary response dict.
        """
        return {
            "success": True,
            "intent": intent,
            "data": data if data else {},
            "summary": summary,
            "suggestions": suggestions or [],
        }

    @staticmethod
    def build_validation_error(
        intent: str,
        errors: list[str],
        suggestions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Build a validation error response.

        Args:
            intent: The classified intent name.
            errors: List of validation error messages.
            suggestions: Optional list of suggested next actions.

        Returns:
            Standardized validation error response dict.
        """
        return {
            "success": False,
            "intent": intent,
            "data": {"validation_errors": errors},
            "summary": "; ".join(errors),
            "suggestions": suggestions or [],
        }

    @staticmethod
    def build_empty(intent: str) -> dict[str, Any]:
        """Build a response indicating no data was found.

        Args:
            intent: The classified intent name.

        Returns:
            Standardized empty response dict.
        """
        return {
            "success": True,
            "intent": intent,
            "data": {},
            "summary": "No data found.",
            "suggestions": [],
        }
