# auth_service.py - Service layer for authentication operations.

from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import AuthenticationError, ValidationError
from app.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET,
    LOCKOUT_DURATION_MINUTES,
    MAX_LOGIN_ATTEMPTS,
)
from app.models.dto.auth import TokenPayload
from app.models.schemas.auth import AuthenticatedUser, TokenResponse
from app.models.sqlalchemy.audit_log import AuditLog
from app.repository.audit_log_repo import AuditLogRepository
from app.repository.official_repo import OfficialRepository

logger = structlog.get_logger()

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


class AuthService:
    """Handles login, token generation/validation, refresh, and password changes."""

    def __init__(
        self,
        official_repo: OfficialRepository,
        session: AsyncSession,
        audit_log_repo: AuditLogRepository | None = None,
    ):
        self.official_repo = official_repo
        self.session = session
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

    # ── Login ──

    async def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate an official and return a JWT token pair."""
        official = await self.official_repo.get_official_by_username(
            self.session, username,
        )

        # Unknown username
        if not official:
            await self._audit_login_failed(username=username)
            raise AuthenticationError("Invalid username or password")

        # Account locked?
        now = datetime.now(timezone.utc)
        if official.locked_until and official.locked_until > now:
            await self._audit_login_failed(
                username=username, official_id=official.id, reason="account_locked",
            )
            remaining = int((official.locked_until - now).total_seconds() // 60) + 1
            raise AuthenticationError(
                f"Account is locked. Try again in {remaining} minute(s)."
            )

        # Account deactivated?
        if not official.is_active:
            await self._audit_login_failed(
                username=username, official_id=official.id, reason="account_inactive",
            )
            raise AuthenticationError("Account has been deactivated")

        # Verify password
        if not self._verify_password(password, official.password_hash):
            new_attempts = official.failed_login_attempts + 1
            update_data = {"failed_login_attempts": new_attempts}

            # Lock account if max attempts exceeded
            if new_attempts >= MAX_LOGIN_ATTEMPTS:
                update_data["locked_until"] = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                logger.warning(
                    "Account locked due to failed login attempts",
                    username=username,
                    attempts=new_attempts,
                )

            await self.official_repo.update_official(
                self.session, official.id, update_data,
            )
            await self._audit_login_failed(
                username=username, official_id=official.id, reason="bad_password",
            )
            raise AuthenticationError("Invalid username or password")

        # Success — reset failed attempts, update last_login_at
        await self.official_repo.update_official(
            self.session, official.id, {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login_at": now,
            },
        )

        tokens = self._create_token_pair(official.id, official.username, official.role)

        # Audit: successful login
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="OFFICIAL_LOGIN",
                action="LOGIN",
                summary=f"Official '{username}' logged in",
                resource_type="official",
                resource_id=official.id,
                actor_type="OFFICIAL",
                actor_id=official.id,
            ),
        )

        return tokens

    # ── Token refresh ──

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Exchange a valid refresh token for a new token pair."""
        payload = self.decode_token(refresh_token)

        if payload.token_type != "refresh":
            raise AuthenticationError("Invalid token type — expected a refresh token")

        # Verify the official still exists and is active
        official_id = UUID(payload.sub)
        official = await self.official_repo.get_official_by_id(
            self.session, official_id,
        )
        if not official.is_active:
            raise AuthenticationError("Account has been deactivated")

        return self._create_token_pair(official.id, official.username, official.role)

    # ── Password change ──

    async def change_password(
        self, official_id: UUID, current_password: str, new_password: str,
    ) -> None:
        """Change the password for an official."""
        official = await self.official_repo.get_official_by_id(
            self.session, official_id,
        )

        if not self._verify_password(current_password, official.password_hash):
            raise AuthenticationError("Current password is incorrect")

        if current_password == new_password:
            raise ValidationError("New password must be different from the current password")

        new_hash = _ph.hash(new_password)
        await self.official_repo.update_official(
            self.session, official.id, {
                "password_hash": new_hash,
                "must_reset_password": False,
            },
        )

        logger.info("Password changed", official_id=str(official_id))

    # ── Token creation / decoding ──

    def _create_token_pair(
        self, official_id: UUID, username: str, role: str,
    ) -> TokenResponse:
        """Create an access + refresh JWT pair."""
        now = datetime.now(timezone.utc)

        access_payload = {
            "sub": str(official_id),
            "username": username,
            "role": role,
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        }
        refresh_payload = {
            "sub": str(official_id),
            "username": username,
            "role": role,
            "token_type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)).timestamp()),
        }

        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """Decode and validate a JWT token. Raises AuthenticationError on failure."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return TokenPayload(
                sub=payload["sub"],
                username=payload["username"],
                role=payload["role"],
                token_type=payload["token_type"],
                exp=payload["exp"],
                iat=payload["iat"],
            )
        except JWTError as exc:
            raise AuthenticationError(f"Invalid or expired token") from exc

    # ── Password helpers ──

    @staticmethod
    def _verify_password(password: str, stored_hash: str | None) -> bool:
        """Verify a password against an Argon2id hash."""
        if not stored_hash:
            return False
        try:
            return _ph.verify(stored_hash, password)
        except VerifyMismatchError:
            return False

    # ── Audit helpers ──

    async def _audit_login_failed(
        self,
        username: str,
        official_id: UUID | None = None,
        reason: str = "invalid_credentials",
    ) -> None:
        """Record a failed login attempt in the audit log."""
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="OFFICIAL_LOGIN_FAILED",
                action="LOGIN",
                summary=f"Failed login for '{username}' ({reason})",
                resource_type="official",
                resource_id=official_id,
                actor_type="OFFICIAL",
                event_metadata={"username": username, "reason": reason},
            ),
        )
