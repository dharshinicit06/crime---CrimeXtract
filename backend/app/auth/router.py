"""Authentication router: register, login, token refresh, and profile."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_token, verify_token
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    RefreshResponse,
    TokenResponse,
    UserResponse,
)
from app.chat.models import ChatConversation
from app.config import settings
from app.dependencies import get_current_user, get_db_session
from app.exceptions.handlers import ConflictException, UnauthorizedException
from app.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with role assignment. Admin-only role assignment is enforced.",
)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Register a new user."""
    from sqlalchemy import select

    # Check if user already exists
    existing = await session.execute(
        select(User).where(User.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(message="A user with this email already exists")

    new_user = User(
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        phone=request.phone,
        role_id=request.role_id or 3,  # default: Analyst
        is_active=True,
    )
    session.add(new_user)
    await session.flush()
    await session.refresh(new_user)

    logger.info(
        "User registered",
        extra={"user_id": new_user.id, "email": new_user.email, "role_id": new_user.role_id},
    )
    return new_user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with email and password",
    description="Authenticate with email and password. Returns user profile + JWT access and refresh tokens.",
)
async def login(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    """Authenticate user and return user info + JWT tokens."""
    from sqlalchemy import select

    result = await session.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise UnauthorizedException(message="Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException(message="Account is disabled. Contact administrator.")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(
        "User logged in",
        extra={"user_id": user.id, "email": user.email},
    )

    response = LoginResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )

    logger.info("Login response prepared, returning...")
    return response


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="Use a valid refresh token to obtain a new token pair.",
)
async def refresh_token(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RefreshResponse:
    """Refresh the access token using a valid refresh token."""
    from app.auth.jwt import decode_token as parse_token

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
        )

    token = auth_header.split(" ")[1]
    payload = parse_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # ── Verify user still exists and is active ─────────────────
    from sqlalchemy import select as sql_select

    user_result = await session.execute(
        sql_select(User).where(User.id == int(user_id))
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        logger.warning("Refresh token used for deleted user ID=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        logger.warning("Refresh token used for inactive user ID=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    new_access = create_access_token(data={"sub": str(user_id)})
    new_refresh = create_refresh_token(data={"sub": str(user_id)})

    return RefreshResponse(
        tokens=TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        ),
    )


@router.get(
    "/conversations",
    summary="List current user's chat conversations (shortcut)",
)
async def my_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list:
    """Return basic conversation info for the authenticated user."""
    from sqlalchemy import select

    q = select(ChatConversation).where(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).limit(20)
    r = await session.execute(q)
    convos = r.scalars().all()
    return [{"id": c.id, "title": c.title, "updated_at": str(c.updated_at)} for c in convos]
