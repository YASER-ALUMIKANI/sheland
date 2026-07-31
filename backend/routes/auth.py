"""
CityLand Backend - Authentication & User Management Routes
"""
import re
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

ACCESS_TOKEN_MAX_AGE = 30 * 60  # 30 minutes
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60  # 7 days

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set HttpOnly, Secure, SameSite cookies for access and refresh tokens."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/auth/refresh"
    )

def _clear_auth_cookies(response: Response):
    """Clear auth cookies on logout."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")

from ..database import get_db
from .. import models, schemas, auth
from backend.main import limiter

logger = logging.getLogger("sheland.api")

router = APIRouter()

SAFE_PUBLIC_ROLES = {"customer", "seller"}
ADMIN_MANAGED_ROLES = {"admin", "super_admin", "sales_manager", "seller", "customer"}


@router.post("/api/auth/register", response_model=schemas.Token, status_code=201)
@limiter.limit("30/minute")
def register_user(request: Request, user_in: schemas.UserCreate, response: Response, db: Session = Depends(get_db)):

    """Public self-registration endpoint for Customers and Sellers only."""
    requested_role = (user_in.role or "customer").lower().strip()
    if requested_role in {"admin", "super_admin", "sales_manager"}:
        audit_entry = models.AuditLog(
            action="role_escalation_attempt",
            performed_by=None,
            new_value=requested_role,
            ip_address=request.client.host if (request and request.client) else "unknown",
            details=f"Blocked public registration attempt with admin role '{requested_role}' for email '{user_in.email}'"
        )
        db.add(audit_entry)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="التسجيل الذاتي بالأدوار الإدارية غير مسموح به. يرجى التواصل مع إدارة المتجر."
        )

    final_role = requested_role if requested_role in SAFE_PUBLIC_ROLES else "customer"

    existing_user = db.query(models.User).filter(
        (models.User.email == user_in.email) | (models.User.phone == user_in.phone)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني أو رقم الهاتف مسجل بالفعل")

    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        password_hash=auth.hash_password(user_in.password),
        role=final_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.role == "seller":
        seller = models.Seller(user_id=new_user.id, store_name=f"متجر {new_user.name}")
        db.add(seller)
        db.commit()

    user_agent = request.headers.get("user-agent") if request else None
    access_token = auth.create_access_token({"sub": str(new_user.id), "role": new_user.role})
    refresh_token = auth.create_refresh_token({"sub": str(new_user.id), "role": new_user.role}, user_agent=user_agent)
    result = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user
    }
    _set_auth_cookies(response, access_token, refresh_token)
    return result


@router.post("/api/auth/login", response_model=schemas.Token)
@limiter.limit("15/minute")
def login_user(request: Request, login_in: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate user with email/phone & password, returning JWT token with audit logging."""
    clean_identifier = login_in.email_or_phone.strip().lower()
    clean_phone = login_in.email_or_phone.strip()
    client_ip = request.client.host if (request and request.client) else "unknown"

    user = db.query(models.User).filter(
        (func.lower(models.User.email) == clean_identifier) | (models.User.phone == clean_phone)
    ).first()
    
    if not user or not auth.verify_password(login_in.password.strip(), user.password_hash):
        masked_id = clean_identifier[:3] + "***" if len(clean_identifier) > 3 else "***"
        logger.warning(f"🚨 Security Audit: Failed login attempt for user/identifier '{masked_id}' from IP={client_ip}")
        raise HTTPException(
            status_code=401,
            detail="بيانات الدخول غير صحيحة (البريد الإلكتروني/رقم الجوال أو كلمة المرور خطأ)"
        )
    
    user_agent = request.headers.get("user-agent") if request else None
    access_token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = auth.create_refresh_token({"sub": str(user.id), "role": user.role}, user_agent=user_agent)
    logger.info(f"✅ Security Audit: Successful login for user_id={user.id}, role={user.role} from IP={client_ip}")
    result = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }
    _set_auth_cookies(response, access_token, refresh_token)
    return result


@router.post("/api/auth/refresh", response_model=schemas.Token)
@limiter.limit("20/minute")
def refresh_token(
    request: Request,
    refresh_in: schemas.TokenRefreshRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refreshes short-lived Access Token and rotates Refresh Token with User-Agent binding."""
    user_agent = request.headers.get("user-agent") if request else None
    refresh_token_val = refresh_in.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token_val:
        raise HTTPException(status_code=401, detail="رمز الإنعاش مفقود")
    payload = auth.decode_refresh_token(refresh_token_val, user_agent=user_agent)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=401,
            detail="رمز الإنعاش (Refresh Token) غير صالح أو منتهي الصلاحية أو تم إبطاله"
        )

    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="رمز الإنعاش غير صالح")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")

    auth.revoke_token(refresh_token_val)

    new_access_token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh_token = auth.create_refresh_token({"sub": str(user.id), "role": user.role}, user_agent=user_agent)

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    result = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return result


@router.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.require_current_user)):
    """Return currently authenticated user profile."""
    return current_user


@router.put("/api/auth/profile", response_model=schemas.UserResponse)
def update_user_profile(
    profile_in: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_current_user)
):
    """Updates authenticated user's profile info (name, phone) and updates their orders' phone numbers and shipping_address strings."""
    if profile_in.name:
        current_user.name = profile_in.name.strip()
    if profile_in.phone:
        clean_phone = profile_in.phone.strip()
        old_phone = current_user.phone
        current_user.phone = clean_phone
        
        orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
        for order in orders:
            order.phone = clean_phone
            if order.shipping_address:
                if old_phone and old_phone in order.shipping_address:
                    order.shipping_address = order.shipping_address.replace(old_phone, clean_phone)
                else:
                    order.shipping_address = re.sub(r'\(\+?\d{6,14}\)', f'({clean_phone})', order.shipping_address)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/api/auth/change-password")
def change_password(
    password_in: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_current_user)
):
    """Change the current user's own password. Requires current password verification."""
    if not auth.verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")

    current_user.password_hash = auth.hash_password(password_in.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/api/auth/logout")
def logout_user(request: Request, response: Response, token: Optional[str] = Depends(auth.oauth2_scheme)):
    """Logout current user and invalidate (blacklist) their JWT access token + clear cookies."""
    if not token:
        token = request.cookies.get("access_token")
    if token:
        auth.revoke_token(token)
    _clear_auth_cookies(response)
    return {"message": "تم تسجيل الخروج وإلغاء صلاحية التوكن بنجاح."}
