"""
CityLand Backend - JWT Authentication & Password Hashing
# ponytail: Simple, self-contained JWT and password utility for low overhead
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models

# ponytail: Read secret from env or use strong fallback for development
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sheland-secure-jwt-secret-key-2026-cityland")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days expiration

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    """Hash plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT access token."""
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
