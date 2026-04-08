# auth_route.py - Authentication routes (login, refresh, change password, me).

from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, status

from app.application.api.dependencies import get_auth_service, get_current_user
from app.models.dto.auth import TokenPayload
from app.models.schemas.auth import (
    AuthenticatedUser,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.service.auth_service import AuthService

logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# Temporary diagnostic + seed endpoint
@router.get("/debug-db")
async def debug_db(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: show which DB and officials exist."""
    from app.config import DATABASE_URL
    from sqlalchemy import text
    result = await service.session.execute(text("SELECT username, role FROM election_official ORDER BY username"))
    officials = [{"username": r[0], "role": r[1]} for r in result]
    return {"database_url": DATABASE_URL[:50] + "...", "officials": officials}


@router.get("/seed-officials")
async def seed_officials(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: seed officials into whatever DB the app connects to."""
    from argon2 import PasswordHasher
    from uuid import uuid4
    from sqlalchemy import text

    ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    officials = [
        ("admin1", "ADMIN", "Password1"),
        ("admin2", "ADMIN", "Password1"),
        ("officer1", "OFFICER", "Password1"),
        ("officer2", "OFFICER", "Password1"),
        ("officer3", "OFFICER", "Password1"),
    ]
    created = []
    for username, role, password in officials:
        pwd_hash = ph.hash(password)
        await service.session.execute(
            text("""INSERT INTO election_official
                    (id, username, password_hash, role, is_active, must_reset_password, failed_login_attempts, created_at, updated_at)
                    VALUES (:id, :u, :p, :r, TRUE, FALSE, 0, NOW(), NOW())
                    ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash, failed_login_attempts = 0, locked_until = NULL"""),
            {"id": str(uuid4()), "u": username, "p": pwd_hash, "r": role},
        )
        created.append(username)
    return {"seeded": created, "message": "Officials seeded. Try admin1/Password1"}


# Login — public (no token required)
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    body: LoginRequest = Body(..., description="Login credentials."),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with username and password.

    Returns a JWT access token and refresh token.
    Failed attempts are tracked; the account locks after repeated failures.
    """
    return await service.login(body.username, body.password)


# Refresh — public (uses refresh token in body, not bearer)
@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    body: RefreshTokenRequest = Body(..., description="Refresh token."),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return await service.refresh_token(body.refresh_token)


# Get current user profile — protected
@router.get(
    "/me",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_200_OK,
)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
) -> AuthenticatedUser:
    """Return the currently authenticated user's profile from the JWT."""
    return AuthenticatedUser(
        id=current_user.sub,
        username=current_user.username,
        role=current_user.role,
        must_reset_password=False,
    )


# Change password — protected
@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    body: ChangePasswordRequest = Body(..., description="Password change request."),
    current_user: TokenPayload = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ChangePasswordResponse:
    """Change the currently authenticated user's password."""
    await service.change_password(
        official_id=UUID(current_user.sub),
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return ChangePasswordResponse(detail="Password changed successfully")
