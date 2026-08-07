"""
CityLand Backend - Token Refresh, Security Blacklist & Cookies Tests
"""
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient

from backend.auth import create_access_token


def test_refresh_token_with_wrong_ua_rejected(client: TestClient):
    """Verifies that a refresh token created with a specific User-Agent is rejected if presented with a different User-Agent."""
    # 1. Register user with User-Agent A
    headers_a = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "name": "UA Test User",
            "email": "ua_user@example.com",
            "phone": "967771112233",
            "password": "SecurePassword123"
        },
        headers=headers_a
    )
    assert reg_resp.status_code == 201
    refresh_token = reg_resp.json()["refresh_token"]

    # 2. Attempt refresh with User-Agent B (mismatch)
    headers_b = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1"}
    refresh_resp = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
        headers=headers_b
    )
    assert refresh_resp.status_code == 401
    assert "رمز الإنعاش" in refresh_resp.json()["detail"] or "غير صالح" in refresh_resp.json()["detail"]


def test_logout_blacklists_access_token(client: TestClient):
    """Verifies that calling logout invalidates the access token, blocking subsequent protected requests."""
    # 1. Register & login user
    email = "logout_user@sheland.com"
    pwd = "LogoutPassword123"
    client.post(
        "/api/auth/register",
        json={"name": "Logout User", "email": email, "phone": "967772223344", "password": pwd}
    )

    login_resp = client.post(
        "/api/auth/login",
        json={"email_or_phone": email, "password": pwd}
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Verify access to protected endpoint before logout
    me_resp_1 = client.get("/api/auth/me", headers=headers)
    assert me_resp_1.status_code == 200

    # 3. Perform logout
    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # 4. Verify that access token is now blacklisted and rejected
    me_resp_2 = client.get("/api/auth/me", headers=headers)
    assert me_resp_2.status_code == 401


def test_expired_access_token_returns_401(client: TestClient):
    """Verifies that an expired JWT access token is rejected with HTTP 401."""
    # Create token expired 10 seconds ago
    expired_token = create_access_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=timedelta(seconds=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_refresh_token_rotation_invalidates_old(client: TestClient):
    """Verifies that refreshing tokens rotates the refresh token and revokes the old one."""
    # 1. Register & login user
    email = "rotate_user@sheland.com"
    pwd = "RotatePassword123"
    client.post(
        "/api/auth/register",
        json={"name": "Rotate User", "email": email, "phone": "967773334455", "password": pwd}
    )

    login_resp = client.post(
        "/api/auth/login",
        json={"email_or_phone": email, "password": pwd}
    )
    assert login_resp.status_code == 200
    old_refresh_token = login_resp.json()["refresh_token"]

    # 2. Refresh token to receive a new pair
    refresh_resp_1 = client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh_token}
    )
    assert refresh_resp_1.status_code == 200
    new_refresh_token = refresh_resp_1.json()["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # 3. Attempt to reuse old_refresh_token -> Must fail with 401
    refresh_resp_2 = client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh_token}
    )
    assert refresh_resp_2.status_code == 401


def test_access_token_cookie_is_httponly(client: TestClient):
    """Verifies that login sets access_token and refresh_token cookies with HttpOnly flag."""
    email = "cookie_user@sheland.com"
    pwd = "CookiePassword123"
    client.post(
        "/api/auth/register",
        json={"name": "Cookie User", "email": email, "phone": "967774445566", "password": pwd}
    )

    login_resp = client.post(
        "/api/auth/login",
        json={"email_or_phone": email, "password": pwd}
    )
    assert login_resp.status_code == 200

    set_cookie_headers = [
        val for key, val in login_resp.headers.raw
        if key.decode('ascii').lower() == 'set-cookie'
    ]
    assert len(set_cookie_headers) >= 1

    cookies_text = " ".join([h.decode('utf-8') for h in set_cookie_headers])
    assert "access_token=" in cookies_text
    assert "httponly" in cookies_text.lower()

