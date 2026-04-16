"""Unit tests for AuthService — login, lockout, token lifecycle, password change."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from argon2 import PasswordHasher

from app.application.core.exceptions import AuthenticationError, ValidationError
from app.service.auth_service import AuthService

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_official(
    *,
    password: str = "CorrectPassword1!",
    is_active: bool = True,
    failed_login_attempts: int = 0,
    locked_until: datetime | None = None,
    must_reset_password: bool = False,
):
    obj = MagicMock()
    obj.id = uuid.uuid4()
    obj.username = "admin"
    obj.password_hash = _ph.hash(password)
    obj.role = "ADMIN"
    obj.is_active = is_active
    obj.failed_login_attempts = failed_login_attempts
    obj.locked_until = locked_until
    obj.must_reset_password = must_reset_password
    return obj


def _make_service(session, official_repo=None) -> AuthService:
    official_repo = official_repo or AsyncMock()
    audit_log_repo = AsyncMock()
    return AuthService(
        official_repo=official_repo,
        session=session,
        audit_log_repo=audit_log_repo,
    )


# ---------------------------------------------------------------------------
# Login — success
# ---------------------------------------------------------------------------

class TestLoginSuccess:
    async def test_login_returns_token_pair(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        result = await svc.login("admin", "CorrectPassword1!")

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.expires_in > 0

    async def test_login_resets_failed_attempts_on_success(self, mock_session):
        official = _make_official(failed_login_attempts=3)
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        await svc.login("admin", "CorrectPassword1!")

        # Verify failed_login_attempts was reset to 0
        repo.update_official.assert_called_once()
        update_data = repo.update_official.call_args[0][2]
        assert update_data["failed_login_attempts"] == 0
        assert update_data["locked_until"] is None


# ---------------------------------------------------------------------------
# Login — failure cases
# ---------------------------------------------------------------------------

class TestLoginFailure:
    async def test_login_unknown_username_raises(self, mock_session):
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=None)
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await svc.login("unknown_user", "anything")

    async def test_login_wrong_password_raises(self, mock_session):
        official = _make_official(password="CorrectPassword1!")
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await svc.login("admin", "WrongPassword!")

    async def test_login_wrong_password_increments_failed_attempts(self, mock_session):
        official = _make_official(password="CorrectPassword1!", failed_login_attempts=2)
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError):
            await svc.login("admin", "WrongPassword!")

        update_data = repo.update_official.call_args[0][2]
        assert update_data["failed_login_attempts"] == 3

    async def test_login_inactive_account_raises(self, mock_session):
        official = _make_official(is_active=False)
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError, match="deactivated"):
            await svc.login("admin", "CorrectPassword1!")


# ---------------------------------------------------------------------------
# Account lockout
# ---------------------------------------------------------------------------

class TestAccountLockout:
    async def test_login_locked_account_raises(self, mock_session):
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        official = _make_official(locked_until=locked_until)
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError, match="locked"):
            await svc.login("admin", "CorrectPassword1!")

    async def test_fifth_failed_attempt_locks_account(self, mock_session):
        official = _make_official(
            password="CorrectPassword1!",
            failed_login_attempts=4,  # next failure = 5th = lockout
        )
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError):
            await svc.login("admin", "WrongPassword!")

        update_data = repo.update_official.call_args[0][2]
        assert update_data["failed_login_attempts"] == 5
        assert update_data["locked_until"] is not None
        assert update_data["locked_until"] > datetime.now(timezone.utc)

    async def test_expired_lockout_allows_login(self, mock_session):
        # Lockout expired 1 minute ago
        locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        official = _make_official(locked_until=locked_until)
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        result = await svc.login("admin", "CorrectPassword1!")
        assert result.access_token


# ---------------------------------------------------------------------------
# Token decode
# ---------------------------------------------------------------------------

class TestTokenDecode:
    async def test_decode_valid_access_token(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")
        payload = svc.decode_token(tokens.access_token)

        assert payload.sub == str(official.id)
        assert payload.username == "admin"
        assert payload.role == "ADMIN"
        assert payload.token_type == "access"

    async def test_decode_valid_refresh_token(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")
        payload = svc.decode_token(tokens.refresh_token)

        assert payload.token_type == "refresh"
        assert payload.sub == str(official.id)

    async def test_decode_tampered_token_raises(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")
        tampered = tokens.access_token[:-5] + "XXXXX"

        with pytest.raises(AuthenticationError, match="Invalid or expired token"):
            svc.decode_token(tampered)

    def test_decode_garbage_token_raises(self):
        with pytest.raises(AuthenticationError):
            AuthService.decode_token("not.a.valid.jwt")


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

class TestTokenRefresh:
    async def test_refresh_with_valid_refresh_token(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.get_official_by_id = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")
        new_tokens = await svc.refresh_token(tokens.refresh_token)

        # New token pair is issued successfully
        assert new_tokens.access_token
        assert new_tokens.refresh_token
        assert new_tokens.token_type == "bearer"
        assert new_tokens.expires_in > 0

    async def test_refresh_with_access_token_raises(self, mock_session):
        official = _make_official()
        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")

        with pytest.raises(AuthenticationError, match="refresh token"):
            await svc.refresh_token(tokens.access_token)

    async def test_refresh_deactivated_account_raises(self, mock_session):
        official = _make_official()
        deactivated_official = _make_official(is_active=False)
        deactivated_official.id = official.id
        deactivated_official.username = official.username

        repo = AsyncMock()
        repo.get_official_by_username = AsyncMock(return_value=official)
        repo.get_official_by_id = AsyncMock(return_value=deactivated_official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        tokens = await svc.login("admin", "CorrectPassword1!")

        with pytest.raises(AuthenticationError, match="deactivated"):
            await svc.refresh_token(tokens.refresh_token)


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------

class TestPasswordChange:
    async def test_change_password_success(self, mock_session):
        official = _make_official(password="OldPassword1!")
        repo = AsyncMock()
        repo.get_official_by_id = AsyncMock(return_value=official)
        repo.update_official = AsyncMock()
        svc = _make_service(mock_session, repo)

        await svc.change_password(official.id, "OldPassword1!", "NewPassword2!")

        repo.update_official.assert_called_once()
        update_data = repo.update_official.call_args[0][2]
        assert "password_hash" in update_data
        assert update_data["must_reset_password"] is False

    async def test_change_password_wrong_current_raises(self, mock_session):
        official = _make_official(password="OldPassword1!")
        repo = AsyncMock()
        repo.get_official_by_id = AsyncMock(return_value=official)
        svc = _make_service(mock_session, repo)

        with pytest.raises(AuthenticationError, match="incorrect"):
            await svc.change_password(official.id, "WrongCurrent!", "NewPassword2!")

    async def test_change_password_same_as_current_raises(self, mock_session):
        official = _make_official(password="SamePassword1!")
        repo = AsyncMock()
        repo.get_official_by_id = AsyncMock(return_value=official)
        svc = _make_service(mock_session, repo)

        with pytest.raises(ValidationError, match="different"):
            await svc.change_password(official.id, "SamePassword1!", "SamePassword1!")
