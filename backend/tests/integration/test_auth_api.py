"""Integration tests for the auth API endpoints via FastAPI TestClient.

These tests use dependency overrides to mock the database layer,
verifying that the HTTP layer (routes, error handlers, status codes)
works correctly end-to-end without requiring a live database.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from app.application.api.dependencies import get_db, get_session_factory
from app.application.core.exceptions import AuthenticationError
from app.service.auth_service import AuthService
from main import app

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_official(
    password: str = "TestPassword1!",
    is_active: bool = True,
    failed_login_attempts: int = 0,
    locked_until=None,
):
    obj = MagicMock()
    obj.id = uuid.uuid4()
    obj.username = "testadmin"
    obj.password_hash = _ph.hash(password)
    obj.role = "ADMIN"
    obj.is_active = is_active
    obj.failed_login_attempts = failed_login_attempts
    obj.locked_until = locked_until
    obj.must_reset_password = False
    obj.last_login_at = None
    return obj


@pytest.fixture
def client():
    """TestClient with database dependencies overridden."""
    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.begin = MagicMock()

    mock_factory = MagicMock()

    async def override_db():
        yield mock_session

    def override_factory(request=None):
        return mock_factory

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_session_factory] = override_factory

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

class TestLoginEndpoint:
    def test_login_success_returns_200(self, client):
        official = _make_official()
        with _patch_auth_service_login(official):
            resp = client.post(
                "/api/v1/auth/login",
                json={"username": "testadmin", "password": "TestPassword1!"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials_returns_401(self, client):
        with _patch_auth_service_login_fail():
            resp = client.post(
                "/api/v1/auth/login",
                json={"username": "bad", "password": "wrong"},
            )
        assert resp.status_code == 401
        assert "AUTHENTICATION_ERROR" in resp.json().get("code", "")

    def test_login_missing_username_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"password": "something"},
        )
        assert resp.status_code == 422

    def test_login_missing_password_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )
        assert resp.status_code == 422

    def test_login_empty_body_returns_422(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------

class TestRefreshEndpoint:
    def test_refresh_with_invalid_token_returns_401(self, client):
        with _patch_auth_service_refresh_fail():
            resp = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid.jwt.token"},
            )
        assert resp.status_code == 401

    def test_refresh_missing_token_returns_422(self, client):
        resp = client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------

class TestMeEndpoint:
    def test_me_without_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.here"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Helpers — patch the auth service at the dependency level
# ---------------------------------------------------------------------------

from unittest.mock import patch
from app.application.api.dependencies import get_auth_service
from app.models.schemas.auth import TokenResponse


def _patch_auth_service_login(official):
    """Context manager that overrides get_auth_service to return a mock
    that successfully logs in and returns tokens."""
    mock_svc = AsyncMock(spec=AuthService)
    mock_svc.login = AsyncMock(return_value=TokenResponse(
        access_token="test.access.token",
        refresh_token="test.refresh.token",
        token_type="bearer",
        expires_in=1800,
    ))

    async def override():
        return mock_svc

    app.dependency_overrides[get_auth_service] = override
    return _OverrideCleanup(get_auth_service)


def _patch_auth_service_login_fail():
    """Context manager that makes login raise AuthenticationError."""
    mock_svc = AsyncMock(spec=AuthService)
    mock_svc.login = AsyncMock(side_effect=AuthenticationError("Invalid username or password"))

    async def override():
        return mock_svc

    app.dependency_overrides[get_auth_service] = override
    return _OverrideCleanup(get_auth_service)


def _patch_auth_service_refresh_fail():
    """Context manager that makes refresh raise AuthenticationError."""
    mock_svc = AsyncMock(spec=AuthService)
    mock_svc.refresh_token = AsyncMock(side_effect=AuthenticationError("Invalid or expired token"))

    async def override():
        return mock_svc

    app.dependency_overrides[get_auth_service] = override
    return _OverrideCleanup(get_auth_service)


class _OverrideCleanup:
    """Tiny context manager that removes a dependency override on exit."""
    def __init__(self, dep_key):
        self._key = dep_key
    def __enter__(self):
        return self
    def __exit__(self, *args):
        app.dependency_overrides.pop(self._key, None)
