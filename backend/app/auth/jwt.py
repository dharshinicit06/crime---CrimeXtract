"""Auth-domain JWT helpers wrapping core security."""

from typing import Any, Dict, Optional

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def create_tokens(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Create an access + refresh token pair.

    The JWT subject is a stringified user_id.
    Extra claims typically include email, role_id, full_name.
    """
    data: Dict[str, Any] = {"sub": subject}
    if extra_claims:
        data.update(extra_claims)
    return {
        "access_token": create_access_token(data=data),
        "refresh_token": create_refresh_token(data=data),
    }


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token, returning its payload."""
    return decode_token(token)
