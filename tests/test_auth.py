"""
CityLand Backend - Unit Tests for JWT Authentication & Password Hashing
# ponytail: Clean, compact pytest test suite for auth functionality
"""
import pytest
from backend import auth

def test_hash_and_verify_password():
    password = "secret_password_123"
    hashed = auth.hash_password(password)
    assert hashed != password
    assert auth.verify_password(password, hashed) is True
    assert auth.verify_password("wrong_password", hashed) is False

def test_create_and_decode_jwt_token():
    data = {"sub": "42", "role": "admin"}
    token = auth.create_access_token(data)
    assert isinstance(token, str)
    
    decoded = auth.decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "42"
    assert decoded.get("role") == "admin"

def test_register_user_endpoint(client):
    payload = {
        "name": "تاجر اختبار",
        "email": "test_seller@sheland.com",
        "phone": "0779998887",
        "password": "seller_password_123",
        "role": "seller"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert "access_token" in res_data
    assert res_data["user"]["email"] == "test_seller@sheland.com"
    assert res_data["user"]["role"] == "seller"

def test_login_user_endpoint(client):
    # First register user
    reg_payload = {
        "name": "عميل اختبار",
        "email": "customer@sheland.com",
        "phone": "0771234567",
        "password": "my_password_456",
        "role": "customer"
    }
    client.post("/api/auth/register", json=reg_payload)

    # Login with email
    login_payload = {
        "email_or_phone": "customer@sheland.com",
        "password": "my_password_456"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["user"]["name"] == "عميل اختبار"

def test_get_me_endpoint(client):
    # Register customer and get token
    reg_payload = {
        "name": "مستخدم عادي",
        "email": "user_me_test@sheland.com",
        "phone": "0770001122",
        "password": "user_pass_789",
        "role": "customer"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload).json()
    token = reg_res["access_token"]

    # Request /api/auth/me with Bearer header
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "user_me_test@sheland.com"
    assert user_info["role"] == "customer"


def test_invalid_credentials_login(client):
    login_payload = {
        "email_or_phone": "nonexistent@sheland.com",
        "password": "wrong_password"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 401

def test_token_revocation_and_logout(client):
    data = {"sub": "100", "role": "customer"}
    token = auth.create_access_token(data)
    assert auth.decode_access_token(token) is not None

    # Revoke token
    auth.revoke_token(token)
    assert auth.is_token_revoked(token) is True
    assert auth.decode_access_token(token) is None

    # Test logout API endpoint
    reg_payload = {
        "name": "مستخدم خروج",
        "email": "logout_user@sheland.com",
        "phone": "0778887766",
        "password": "logout_password_123",
        "role": "customer"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload).json()
    user_token = reg_res["access_token"]

    headers = {"Authorization": f"Bearer {user_token}"}
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert "تم تسجيل الخروج" in logout_res.json()["message"]

    # Subsequent request using the revoked token should be rejected (401)
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 401

def test_historical_leaked_secret_is_in_weak_secrets():
    leaked_key = "c3f19e48710ab52d96c4a8f3e271b05a7d91e84239f60e1d8a3b5c7e9f0a2b4c"
    assert leaked_key in auth.WEAK_SECRETS


