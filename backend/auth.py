"""
CityLand Backend - JWT Authentication & Password Hashing
# ponytail: Simple, self-contained JWT and password utility for low overhead
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models

import secrets
import logging

logger = logging.getLogger("sheland.auth")

# Known weak/predictable fallback keys to reject for production safety
WEAK_SECRETS = {
    "sheland_secret_jwt_key_super_secure_2026",
    "sheland-secure-jwt-secret-key-2026-cityland",
    "change_this_to_a_random_secure_secret_key",
    "secret",
    "secretkey",
    "123456",
    "admin123"
}

# Resolve secret from environment (checking JWT_SECRET_KEY first, then SECRET_KEY)
_env_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")

if not _env_secret:
    SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "⚠️ JWT_SECRET_KEY / SECRET_KEY is not set! Auto-generated dynamic key (%s...). "
        "User sessions will be invalidated on server restart. Set SECRET_KEY in .env for persistent tokens.",
        SECRET_KEY[:8]
    )
elif _env_secret in WEAK_SECRETS or len(_env_secret) < 32:
    logger.warning(
        "⚠️ SECURITY WARNING: The configured SECRET_KEY is weak or predictable! "
        "Generating a high-entropy 256-bit dynamic key for this session."
    )
    SECRET_KEY = secrets.token_hex(32)
else:
    SECRET_KEY = _env_secret

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours (1 day expiration)

# In-memory & Cache-backed Token Blacklist / Revocation
_token_blacklist = set()

def revoke_token(token: str) -> bool:
    """Revoke/blacklist a JWT token (e.g. on logout or security invalidation)."""
    if token:
        _token_blacklist.add(token)
        return True
    return False

def is_token_revoked(token: str) -> bool:
    """Check if a JWT token has been revoked/blacklisted."""
    return token in _token_blacklist

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash plain password using native bcrypt."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash or plain text fallback."""
    if not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        # Fallback if hash is plain text or invalid format from legacy database
        return plain_password == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT access token."""
    if not token or is_token_revoked(token):
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[models.User]:
    """FastAPI dependency to extract and return current authenticated user."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        return None
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user

def require_current_user(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    """FastAPI dependency requiring an authenticated user, raising 401 if missing."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="غير مصرح: يلزم تسجيل الدخول أولاً",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

ROLE_HIERARCHY = {
    "super_admin": ["super_admin", "admin", "sales_manager", "seller", "customer"],
    "admin": ["admin", "sales_manager", "seller", "customer"],
    "sales_manager": ["sales_manager", "seller", "customer"],
    "seller": ["seller", "customer"],
    "customer": ["customer"],
}

def require_roles(allowed_roles: List[str]):
    """FastAPI dependency factory enforcing role-based authorization with hierarchy support."""
    def role_checker(user: models.User = Depends(require_current_user)) -> models.User:
        user_effective_roles = ROLE_HIERARCHY.get(user.role, [user.role])
        if not any(role in allowed_roles for role in user_effective_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح: ليس لديك الصلاحية الكافية للوصول لهذا المسار",
            )
        return user
    return role_checker
