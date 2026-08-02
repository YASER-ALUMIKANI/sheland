"""
Sheland Backend - FastAPI Main Application
# ponytail: Clean modular REST endpoints with automated database seeding
"""

import uuid
import os
import shutil
import io
import csv
import re
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("sheland.api")

from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from PIL import Image
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .database import Base, engine, get_db
from . import models, schemas, analytics, auth, cache, payments

# Create database tables automatically
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_and_save_image(file_bytes: bytes, prefix: str = "img") -> str:
    """
    Strict security validation for uploaded images:
    1. Size limit (Max 5MB)
    2. Magic Bytes verification (JPEG, PNG, WEBP, GIF — NO SVG/PHP/HTML)
    3. Pillow image verification & Decompression bomb protection (Max 4096x4096px)
    4. Save with secure random UUID filename in UPLOAD_DIR
    """
    if not file_bytes or len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم الصورة كبير جداً (الحد الأقصى 5 ميجابايت)")

    # Magic Bytes Verification
    ext = None
    if file_bytes.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[:16]:
        ext = ".webp"
    elif file_bytes.startswith(b"GIF87a") or file_bytes.startswith(b"GIF89a"):
        ext = ".gif"

    if not ext:
        raise HTTPException(status_code=400, detail="بصمة الملف غير صالحة. يُسمح فقط برفع صور JPG أو PNG أو WebP أو GIF")

    # Pillow Integrity Check & Decompression Bomb Protection
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        # Re-open after verify() as Pillow requires re-opening for size inspection
        img_check = Image.open(io.BytesIO(file_bytes))
        if img_check.width > 4096 or img_check.height > 4096:
            raise HTTPException(status_code=400, detail="أبعاد الصورة كبيرة جداً (الحد الأقصى 4096×4096 بكسل)")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="الملف المرفوع محتوى صورة غير صالح أو تالف")

    # Save to UPLOAD_DIR with random UUID name
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    return f"/uploads/{filename}"


app = FastAPI(
    title="Sheland Marketplace API",
    description="Backend API and Frontend for Sheland low-price marketplace",
    version="2.0.0"
)

# Rate Limiting Engine with slowapi
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middleware: Strict Security Headers & CORS Logging
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        logging.warning(f"🚨 CORS violation attempt blocked from origin: {origin}")
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https://images.unsplash.com https://*.unsplash.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=(), "
        "accelerometer=(), autoplay=(), encrypted-media=(), "
        "fullscreen=(self), picture-in-picture=(self)"
    )
    return response


# Security Middleware: Request Audit & Performance Logging (CWE-778 Fix)
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    client_ip = request.client.host if (request and request.client) else "unknown"
    
    logger.info(
        f"🌐 API Audit: {request.method} {request.url.path} "
        f"| Status: {response.status_code} "
        f"| Time: {duration:.3f}s "
        f"| IP: {client_ip}"
    )
    return response



# Security Middleware: Anti-CSRF Protection Middleware for State-Changing Requests
EXEMPT_CSRF_PATHS = {"/docs", "/openapi.json", "/redoc"}

@app.middleware("http")
async def csrf_protection_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE"] and request.url.path not in EXEMPT_CSRF_PATHS:
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        x_requested_with = request.headers.get("x-requested-with")

        # 1. Validate Origin header (Cross-Origin Protection)
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "🚨 CSRF Error: Invalid or unauthorized Origin header"}
            )

        # 2. Validate Referer header if Origin is not set
        if referer and not any(referer.startswith(o) for o in ALLOWED_ORIGINS):
            return JSONResponse(
                status_code=403,
                content={"detail": "🚨 CSRF Error: Invalid or unauthorized Referer header"}
            )

        # 3. Enforce X-Requested-With for browser requests (when Origin/Referer/Sec-Fetch-Site is present)
        if (origin or referer or request.headers.get("sec-fetch-site")) and x_requested_with != "XMLHttpRequest":
            return JSONResponse(
                status_code=403,
                content={"detail": "🚨 CSRF Error: Missing or invalid X-Requested-With header"}
            )

        # 4. Explicit check if X-Requested-With is present but with wrong value
        if x_requested_with and x_requested_with != "XMLHttpRequest":
            return JSONResponse(
                status_code=403,
                content={"detail": "🚨 CSRF Error: Missing or invalid X-Requested-With header"}
            )

    return await call_next(request)




# Strict CORS Configuration with Validation, Fail-Closed, Subdomains & Logging
def validate_origin(origin: str) -> bool:
    """Validates origin URL format: scheme://domain[:port]"""
    pattern = r'^https?://[a-zA-Z0-9._-]+(:[0-9]+)?$'
    return bool(re.match(pattern, origin.strip()))

DEFAULT_SAFE_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "https://sheland.com",
    "https://www.sheland.com",
    "https://sheland.onrender.com"
]

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins:
    parsed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    parsed_origins = DEFAULT_SAFE_ORIGINS

# Fail-Closed Validation — NO wildcards allowed
ALLOWED_ORIGINS = [o for o in parsed_origins if validate_origin(o)]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = DEFAULT_SAFE_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


EXCEL_HEADERS = [
    ("title_ar", "اسم المنتج (عربي) *"),
    ("title_en", "اسم المنتج (إنجليزي)"),
    ("category", "القسم / التصنيف *"),
    ("price", "سعر البيع النهائي (ر.ي) *"),
    ("compare_at_price", "السعر قبل الخصم (ر.ي)"),
    ("cost_price", "سعر التكلفة على البائع (ر.ي)"),
    ("stock", "الكمية المتوفرة بالمخزون *"),
    ("sku", "رمز التخزين SKU"),
    ("image_url", "رابط صورة المنتج *"),
    ("description", "وصف وتفاصيل المنتج"),
    ("color", "اللون"),
    ("size", "المقاس"),
    ("free_shipping", "شحن مجاني (نعم/لا)"),
    ("cod_available", "دفع عند الاستلام (نعم/لا)")
]


# Base directory for static frontend files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def ensure_default_users(db: Session):
    """Ensures Admin, Super Admin & Seller default accounts exist with valid bcrypt password hashes without overwriting existing passwords."""
    super_admin = db.query(models.User).filter(models.User.email == "superadmin@sheland.com").first()
    if not super_admin:
        super_admin = models.User(
            name="المدير الفائق",
            email="superadmin@sheland.com",
            phone="0770000001",
            password_hash=auth.hash_password("superadmin123"),
            role="super_admin"
        )
        db.add(super_admin)
        db.commit()

    admin = db.query(models.User).filter(models.User.email == "admin@sheland.com").first()
    if not admin:
        admin = models.User(
            name="مدير منصة شي لاند",
            email="admin@sheland.com",
            phone="0770000000",
            password_hash=auth.hash_password("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()

    seller_user = db.query(models.User).filter(models.User.email == "seller@sheland.com").first()
    if not seller_user:
        seller_user = models.User(
            name="متجر شي لاند الرسمي",
            email="seller@sheland.com",
            phone="0771111111",
            password_hash=auth.hash_password("seller123"),
            role="seller"
        )
        db.add(seller_user)
        db.commit()
        db.refresh(seller_user)

        seller = db.query(models.Seller).filter(models.Seller.user_id == seller_user.id).first()
        if not seller:
            seller = models.Seller(user_id=seller_user.id, store_name="Sheland Official Store", rating=4.8)
            db.add(seller)
            db.commit()


def deduplicate_all_products(db: Session):
    """Merges all duplicate products with the same seller and title_ar, summing their variant stock."""
    products = db.query(models.Product).order_by(models.Product.id.asc()).all()
    grouped = {}
    for p in products:
        key = (p.seller_id, p.title_ar.strip().lower())
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(p)

    merged_count = 0
    for key, prod_list in grouped.items():
        if len(prod_list) > 1:
            main_p = prod_list[0]
            main_variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == main_p.id).first()
            if not main_variant:
                main_variant = models.ProductVariant(product_id=main_p.id, sku=f"SKU-{main_p.id}", stock=10)
                db.add(main_variant)
                db.commit()
                db.refresh(main_variant)

            for dup_p in prod_list[1:]:
                for v in dup_p.variants:
                    main_variant.stock += (v.stock or 0)
                db.query(models.OrderItem).filter(models.OrderItem.product_id == dup_p.id).update({"product_id": main_p.id})
                db.query(models.Review).filter(models.Review.product_id == dup_p.id).update({"product_id": main_p.id})
                db.delete(dup_p)
                merged_count += 1

            db.commit()

    return merged_count


@app.on_event("startup")
def auto_seed_on_startup():
    import threading

    # Run critical seed SYNCHRONOUSLY so it completes before the server accepts traffic
    from .database import SessionLocal, engine, safe_add_column
    try:
        for col, default_val in [
            ("parcel_count", "'1 من 1'"),
            ("weight", "'0.85 كجم'"),
            ("dimensions", "'25 × 15 × 10 سم'"),
        ]:
            safe_add_column(engine, "orders", col, f"VARCHAR DEFAULT {default_val}")

        for col, typedef in [
            ("image_url", "VARCHAR"),
            ("is_verified_purchase", "BOOLEAN DEFAULT 0"),
            ("order_number", "VARCHAR"),
        ]:
            safe_add_column(engine, "reviews", col, typedef)

        for col, typedef in [
            ("coupon_code", "VARCHAR"),
            ("discount_amount", "FLOAT DEFAULT 0.0"),
        ]:
            safe_add_column(engine, "orders", col, typedef)

    except Exception as e:
        logging.warning(f"Migration startup warning: {e}")

    db = SessionLocal()
    try:
        result = _seed_database_internal(db)
        logging.info(f"Startup seed result: {result}")
    except Exception as e:
        logging.error(f"Seed startup error: {e}")
    finally:
        db.close()

    # Deduplicate in background (non-critical)
    def _bg_dedup():
        db2 = SessionLocal()
        try:
            deduplicate_all_products(db2)
        except Exception as e:
            logging.warning(f"Dedup warning: {e}")
        finally:
            db2.close()

    threading.Thread(target=_bg_dedup, daemon=True).start()


# --- Internal Database Seeder ---
def _seed_database_internal(db: Session):
    ensure_default_users(db)

    # Users already created by ensure_default_users, get the seller
    seller_user = db.query(models.User).filter(models.User.email == "seller@sheland.com").first()
    if not seller_user:
        return {"message": "Seller user not found, cannot seed products."}
    db.refresh(seller_user)

    seller = db.query(models.Seller).filter(models.Seller.user_id == seller_user.id).first()
    if not seller:
        seller = models.Seller(user_id=seller_user.id, store_name="Sheland Official Store", rating=4.8)
        db.add(seller)
        db.commit()
        db.refresh(seller)

    has_categories = db.query(models.Category).first() is not None
    has_products = db.query(models.Product).first() is not None

    if has_categories and has_products:
        return {"message": "Default admin and seller accounts verified. Database fully seeded."}

    # Seed Categories (skip if already exist)
    if not has_categories:
        cats_data = [
            {"id": 1, "name_ar": "نساء", "name_en": "Women", "slug": "women", "icon": "👗"},
            {"id": 2, "name_ar": "رجال", "name_en": "Men", "slug": "men", "icon": "👔"},
            {"id": 3, "name_ar": "أطفال", "name_en": "Kids", "slug": "kids", "icon": "🧸"},
            {"id": 4, "name_ar": "المنزل والمطبخ", "name_en": "Home & Kitchen", "slug": "home", "icon": "🏠"},
            {"id": 5, "name_ar": "الجمال والعناية", "name_en": "Beauty", "slug": "beauty", "icon": "💄"},
            {"id": 6, "name_ar": "الإكسسوارات", "name_en": "Accessories", "slug": "accessories", "icon": "⌚"},
            {"id": 7, "name_ar": "الإلكترونيات", "name_en": "Electronics", "slug": "electronics", "icon": "🎧"},
        ]
        for c in cats_data:
            db.add(models.Category(**c))
        db.commit()

    # Seed Products (only if missing)
    if not has_products:
        products_data = [
            # Women
            {"category_id": 1, "title_ar": "فستان صيفي أنيق مزين بالزهور", "title_en": "Elegant Floral Summer Dress", "price": 12000.00, "compare_at_price": 20000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&q=80", "rating": 4.7, "review_count": 840, "is_featured": True},
            {"category_id": 1, "title_ar": "عباية مودرن بخامة حرير ناعمة", "title_en": "Modern Soft Silk Abaya", "price": 22000.00, "compare_at_price": 35000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500&q=80", "rating": 4.9, "review_count": 1250, "is_featured": True},
            {"category_id": 1, "title_ar": "بلوزة كاجوال بأكمام طويلة", "title_en": "Casual Long Sleeve Blouse", "price": 7500.00, "compare_at_price": 12000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=500&q=80", "rating": 4.4, "review_count": 310, "is_featured": False},
            {"category_id": 1, "title_ar": "حقيبة يد نسائية فاخرة بحزام كتف", "title_en": "Luxury Handbag with Shoulder Strap", "price": 16000.00, "compare_at_price": 28000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500&q=80", "rating": 4.8, "review_count": 620, "is_featured": True},
            # Men
            {"category_id": 2, "title_ar": "قميص قطني كاجوال مريح للرجال", "title_en": "Men's Casual Cotton Shirt", "price": 9500.00, "compare_at_price": 16000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500&q=80", "rating": 4.6, "review_count": 520, "is_featured": True},
            {"category_id": 2, "title_ar": "حذاء رياضي خفيف الوزن للمشي", "title_en": "Lightweight Walking Sneakers", "price": 19000.00, "compare_at_price": 30000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&q=80", "rating": 4.8, "review_count": 1420, "is_featured": True},
            {"category_id": 2, "title_ar": "بنطال جينز عصري بقصة مريحة", "title_en": "Modern Relaxed Fit Jeans", "price": 14000.00, "compare_at_price": 22000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&q=80", "rating": 4.5, "review_count": 410, "is_featured": False},
            {"category_id": 2, "title_ar": "سترة شتوية مقاومة للماء والرياح", "title_en": "Waterproof Winter Jacket", "price": 28000.00, "compare_at_price": 45000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=500&q=80", "rating": 4.9, "review_count": 780, "is_featured": True},
            # Kids
            {"category_id": 3, "title_ar": "طقم ملابس أطفال قطني قطعتين", "title_en": "Kids 2-Piece Cotton Outfit", "price": 6500.00, "compare_at_price": 11000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=500&q=80", "rating": 4.7, "review_count": 390, "is_featured": True},
            {"category_id": 3, "title_ar": "لعبة سيارة سباق ذكية بالريموت", "title_en": "Smart Remote Control Car", "price": 11000.00, "compare_at_price": 18000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=500&q=80", "rating": 4.6, "review_count": 210, "is_featured": False},
            # Home & Kitchen
            {"category_id": 4, "title_ar": "طقم أدوات طهي غير لاصقة 8 قطع", "title_en": "8-Piece Non-Stick Cookware Set", "price": 38000.00, "compare_at_price": 58000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500&q=80", "rating": 4.9, "review_count": 1890, "is_featured": True},
            {"category_id": 4, "title_ar": "ماكينة إعداد القهوة الذكية", "title_en": "Smart Espresso Coffee Maker", "price": 45000.00, "compare_at_price": 70000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1517668808822-9ebe02f2a698?w=500&q=80", "rating": 4.8, "review_count": 940, "is_featured": True},
            {"category_id": 4, "title_ar": "مصباح مكتب عصري بإضاءة LED", "title_en": "Modern Desk LED Lamp", "price": 5500.00, "compare_at_price": 9000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&q=80", "rating": 4.5, "review_count": 480, "is_featured": False},
            # Beauty
            {"category_id": 5, "title_ar": "سيروم الهيالورونيك لنضارة البشرة", "title_en": "Hyaluronic Acid Glow Serum", "price": 8500.00, "compare_at_price": 14000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80", "rating": 4.9, "review_count": 2150, "is_featured": True},
            {"category_id": 5, "title_ar": "مجموعة أرواج مات تدوم طويلاً 6 ألوان", "title_en": "6-Color Long Lasting Matte Lipstick Set", "price": 7000.00, "compare_at_price": 12000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&q=80", "rating": 4.7, "review_count": 1100, "is_featured": True},
            # Accessories
            {"category_id": 6, "title_ar": "نظارة شمسية كلاسيكية مع حماية UV", "title_en": "Classic Sunglasses UV Protection", "price": 4800.00, "compare_at_price": 8500.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80", "rating": 4.6, "review_count": 870, "is_featured": True},
            {"category_id": 6, "title_ar": "ساعة يد رجالية كلاسيكية من الفولاذ", "title_en": "Men's Steel Analog Watch", "price": 22000.00, "compare_at_price": 38000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&q=80", "rating": 4.8, "review_count": 730, "is_featured": True},
            # Electronics
            {"category_id": 7, "title_ar": "سماعات لاسلكية مع عزل الضوضاء", "title_en": "Wireless ANC Earbuds", "price": 17000.00, "compare_at_price": 28000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80", "rating": 4.8, "review_count": 3120, "is_featured": True},
            {"category_id": 7, "title_ar": "ساعة ذكية لمتابعة اللياقة والصحة", "title_en": "Smart Fitness & Health Watch", "price": 24000.00, "compare_at_price": 40000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&q=80", "rating": 4.7, "review_count": 1640, "is_featured": True},
            {"category_id": 7, "title_ar": "شاحن سريع لاسلكي للأجهزة الذكية", "title_en": "Fast Wireless Smart Charger", "price": 5800.00, "compare_at_price": 10000.00, "currency": "YER", "image_url": "https://images.unsplash.com/photo-1622445268465-843c61244a70?w=500&q=80", "rating": 4.5, "review_count": 590, "is_featured": False},
        ]

        for p_idx, p in enumerate(products_data):
            slug = f"prod-{p_idx+1}"
            db_p = models.Product(seller_id=seller.id, slug=slug, **p)
            db.add(db_p)
            db.commit()
            db.refresh(db_p)

            v1 = models.ProductVariant(product_id=db_p.id, sku=f"SKU-{db_p.id}-M", color="أسود", size="M", stock=15)
            v2 = models.ProductVariant(product_id=db_p.id, sku=f"SKU-{db_p.id}-L", color="أبيض", size="L", stock=20)
            db.add(v1)
            db.add(v2)
            db.commit()

    # Seed Coupons (only if missing)
    if db.query(models.Coupon).count() == 0:
        c1 = models.Coupon(code="CITY10", discount_type="percent", discount_value=10.0, min_order_amount=0.0)
        c2 = models.Coupon(code="SAVE20", discount_type="fixed", discount_value=20.0, min_order_amount=50.0)
        c3 = models.Coupon(code="CITY25", discount_type="percent", discount_value=25.0, min_order_amount=100.0)
        db.add(c1)
        db.add(c2)
        db.add(c3)
        db.commit()

    return {"status": "success", "message": "Database seeded with products and coupons!"}


# ==========================================================================
# Include Route Modules
# ==========================================================================
from .routes.auth import router as auth_router
from .routes.products import router as products_router
from .routes.orders import router as orders_router
from .routes.reviews import router as reviews_router
from .routes.coupons import router as coupons_router
from .routes.payments import router as payments_router
from .routes.admin import router as admin_router
from .routes.static import router as static_router

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(reviews_router)
app.include_router(coupons_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(static_router)


@app.post("/api/seed")
def manual_seed():
    """Manual seed endpoint - can be called to re-seed missing data."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        result = _seed_database_internal(db)
        product_count = db.query(models.Product).count()
        category_count = db.query(models.Category).count()
        user_count = db.query(models.User).count()
        return {
            **result,
            "counts": {"users": user_count, "categories": category_count, "products": product_count}
        }
    finally:
        db.close()


app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
