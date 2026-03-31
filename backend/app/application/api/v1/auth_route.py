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
