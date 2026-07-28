"""
Sheland Backend - FastAPI Main Application
# ponytail: Clean modular REST endpoints with automated database seeding
"""

import uuid
import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas, analytics

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sheland Marketplace API",
    description="Backend API and Frontend for Sheland low-price marketplace",
    version="2.0.0"
)

# Security Middleware: Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def auto_seed_on_startup():
    from .database import SessionLocal, engine
    # ponytail: Lightweight SQLite schema migration for parcel detail columns
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            for col, default_val in [("parcel_count", "'1 من 1'"), ("weight", "'0.85 كجم'"), ("dimensions", "'25 × 15 × 10 سم'")]:
                try:
                    conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} VARCHAR DEFAULT {default_val}"))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        print("Migration warning:", e)

    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            seed_database(db)
    finally:
        db.close()



# Base directory for static frontend files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to Sheland API", "status": "running"}

@app.get("/admin")
def read_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"message": "Admin dashboard page not found"}

@app.get("/vendor")
def read_vendor():
    vendor_path = os.path.join(FRONTEND_DIR, "vendor.html")
    if os.path.exists(vendor_path):
        return FileResponse(vendor_path)
    return {"message": "Vendor portal page not found"}


@app.get("/styles.css")
def get_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))

@app.get("/app.js")
def get_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))

@app.get("/qrcode.min.js")
def get_qrcode_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "qrcode.min.js"))


@app.get("/manifest.json")
def get_manifest():
    return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
def get_sw():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
    )

@app.get("/icon-192.png")
def get_icon192():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-192.png"), media_type="image/png")

@app.get("/icon-512.png")
def get_icon512():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-512.png"), media_type="image/png")

@app.get("/icon-maskable-192.png")
def get_iconmask192():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-maskable-192.png"), media_type="image/png")

@app.get("/icon-maskable-512.png")
def get_iconmask512():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-maskable-512.png"), media_type="image/png")





# --- Category Endpoints ---
@app.get("/api/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

# --- Product Endpoints ---
@app.get("/api/products", response_model=List[schemas.ProductResponse])
def get_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    free_shipping: Optional[bool] = None,
    cod_available: Optional[bool] = None,
    sort_by: Optional[str] = "relevance",
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (models.Product.title_ar.like(search_pattern)) |
            (models.Product.title_en.like(search_pattern)) |
            (models.Product.description.like(search_pattern))
        )
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(models.Product.rating >= min_rating)
    if free_shipping:
        query = query.filter(models.Product.free_shipping == True)
    if cod_available:
        query = query.filter(models.Product.cod_available == True)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(models.Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(models.Product.price.desc())
    elif sort_by == "rating":
        query = query.order_by(models.Product.rating.desc())
    elif sort_by == "newest":
        query = query.order_by(models.Product.created_at.desc())
    else:
        query = query.order_by(models.Product.is_featured.desc(), models.Product.id.desc())

    products = query.all()
    return [schemas.ProductResponse.from_orm_with_stock(p) for p in products]


@app.get("/api/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return schemas.ProductResponse.from_orm_with_stock(product)

@app.post("/api/products", response_model=schemas.ProductResponse)
def create_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(
        seller_id=product_in.seller_id,
        category_id=product_in.category_id,
        title_ar=product_in.title_ar,
        title_en=product_in.title_en,
        slug=product_in.slug,
        description=product_in.description,
        price=product_in.price,
        compare_at_price=product_in.compare_at_price,
        cost_price=product_in.cost_price if product_in.cost_price is not None else round(product_in.price * 0.6),
        currency=product_in.currency,
        image_url=product_in.image_url,
        free_shipping=product_in.free_shipping,
        cod_available=product_in.cod_available,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    stock_val = getattr(product_in, 'stock', 10)
    if stock_val is None:
        stock_val = 10

    if product_in.variants and len(product_in.variants) > 0:
        for v in product_in.variants:
            db_variant = models.ProductVariant(
                product_id=db_product.id,
                sku=v.sku,
                color=v.color,
                size=v.size,
                stock=v.stock,
                price_override=v.price_override
            )
            db.add(db_variant)
    else:
        db_variant = models.ProductVariant(
            product_id=db_product.id,
            sku=f"SKU-{db_product.id}",
            stock=stock_val
        )
        db.add(db_variant)

    db.commit()
    db.refresh(db_product)
    return schemas.ProductResponse.from_orm_with_stock(db_product)

@app.put("/api/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_product.title_ar = product_in.title_ar
    db_product.title_en = product_in.title_en
    db_product.category_id = product_in.category_id
    db_product.price = product_in.price
    if getattr(product_in, 'cost_price', None) is not None:
        db_product.cost_price = product_in.cost_price
    db_product.compare_at_price = product_in.compare_at_price
    db_product.image_url = product_in.image_url
    db_product.description = product_in.description
    db_product.free_shipping = product_in.free_shipping
    db_product.cod_available = product_in.cod_available

    p_stock = getattr(product_in, 'stock', None)
    if p_stock is not None:
        first_variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).first()
        if first_variant:
            first_variant.stock = p_stock
        else:
            db.add(models.ProductVariant(product_id=product_id, sku=f"SKU-{product_id}", stock=p_stock))

    db.commit()
    db.refresh(db_product)
    return schemas.ProductResponse.from_orm_with_stock(db_product)


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"status": "success", "message": f"Product {product_id} deleted"}

# --- Orders Endpoints ---
@app.get("/api/orders", response_model=List[schemas.OrderResponse])
def get_orders(phone: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if phone:
        clean_phone = phone.strip().replace('+', '')
        query = query.filter(
            (models.Order.phone.like(f"%{clean_phone}%")) |
            (models.Order.shipping_address.like(f"%{clean_phone}%"))
        )
    return query.order_by(models.Order.id.desc()).all()


@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status: str = Query(...), db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return {"status": "success", "order_id": order_id, "new_status": status}

@app.put("/api/orders/{order_id}/parcel-details")
def update_parcel_details(order_id: int, details: schemas.ParcelDetailsUpdate, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if details.parcel_count is not None:
        db_order.parcel_count = details.parcel_count
    if details.weight is not None:
        db_order.weight = details.weight
    if details.dimensions is not None:
        db_order.dimensions = details.dimensions

    db.commit()
    db.refresh(db_order)
    return {
        "status": "success",
        "order_id": order_id,
        "parcel_count": db_order.parcel_count,
        "weight": db_order.weight,
        "dimensions": db_order.dimensions
    }
@app.get("/api/admin/analytics")
def get_admin_analytics(db: Session = Depends(get_db)):
    # ponytail: Delegated to dedicated analytics module for auditability & verification
    return analytics.compute_ecommerce_analytics(db)


@app.get("/api/orders/track/{order_number}", response_model=schemas.OrderResponse)
def track_order(order_number: str, db: Session = Depends(get_db)):

    order = db.query(models.Order).filter(models.Order.order_number == order_number.upper()).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/api/orders", response_model=schemas.OrderResponse)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    # ponytail: Stock validation pass — check exact total available stock across variants
    stock_errors = []
    for item in order_in.items:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"المنتج {item.product_id} غير موجود")
        
        if item.variant_id:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            available = variant.stock if variant else 0
        else:
            available = prod.stock  # computed total stock across all variants

        if item.quantity > available:
            stock_errors.append(
                f"المنتج «{prod.title_ar}»: طلبت {item.quantity} قطعة، المتوفر {available} فقط."
            )

    if stock_errors:
        raise HTTPException(
            status_code=422,
            detail="لا يمكن إتمام الطلب بسبب نقص في المخزون:\n" + "\n".join(stock_errors)
        )

    total = 0.0
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    db_order = models.Order(
        order_number=order_number,
        user_id=order_in.user_id,
        customer_name=order_in.customer_name or "عميل شي لاند",
        phone=order_in.phone or "967770000000",
        shipping_address=order_in.shipping_address,
        payment_method=order_in.payment_method,
        total_amount=total,
        status="قيد المعالجة"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order_in.items:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if prod:
            total += prod.price * item.quantity
            db_item = models.OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                price=prod.price,
                quantity=item.quantity
            )
            db.add(db_item)

            # Deduct stock sequentially from product variants
            remaining_to_deduct = item.quantity
            if item.variant_id:
                variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
                if variant:
                    variant.stock = max(0, variant.stock - remaining_to_deduct)
            else:
                variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == item.product_id).all()
                for v in variants:
                    if remaining_to_deduct <= 0:
                        break
                    deduct = min(v.stock, remaining_to_deduct)
                    v.stock -= deduct
                    remaining_to_deduct -= deduct

    db_order.total_amount = round(total, 2)
    db.commit()
    db.refresh(db_order)
    return db_order

# --- Review Endpoints ---
@app.get("/api/products/{product_id}/reviews", response_model=List[schemas.ReviewResponse])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.Review).filter(models.Review.product_id == product_id).order_by(models.Review.id.desc()).all()

@app.post("/api/products/{product_id}/reviews", response_model=schemas.ReviewResponse)
def create_product_review(product_id: int, review_in: schemas.ReviewCreate, db: Session = Depends(get_db)):
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db_review = models.Review(
        product_id=product_id,
        author_name=review_in.author_name or "عميل شي لاند",
        rating=review_in.rating,
        comment=review_in.comment
    )

    db.add(db_review)

    # Recalculate average rating
    all_revs = db.query(models.Review).filter(models.Review.product_id == product_id).all()
    ratings_list = [r.rating for r in all_revs] + [review_in.rating]
    prod.rating = round(sum(ratings_list) / len(ratings_list), 1)
    prod.review_count = len(ratings_list)

    db.commit()
    db.refresh(db_review)
    return db_review

# --- Coupon Endpoints ---
@app.get("/api/coupons", response_model=List[schemas.CouponResponse])
def get_coupons(db: Session = Depends(get_db)):
    return db.query(models.Coupon).all()

@app.post("/api/coupons/validate")
def validate_coupon(code: str = Query(...), total: float = Query(...), db: Session = Depends(get_db)):
    coupon = db.query(models.Coupon).filter(models.Coupon.code == code.upper(), models.Coupon.is_active == True).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="رمز الكوبون غير صحيح أو منتهي الصلاحية")

    if total < coupon.min_order_amount:
        raise HTTPException(status_code=400, detail=f"الكوبون يتطلب أدنى قيمة طلب {coupon.min_order_amount} ر.س")

    discount = 0.0
    if coupon.discount_type == "percent":
        discount = round(total * (coupon.discount_value / 100.0), 2)
    elif coupon.discount_type == "fixed":
        discount = min(total, coupon.discount_value)

    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount
    }


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/api/upload")
async def upload_image_file(file: UploadFile = File(...)):
    # ponytail: Save uploaded image file directly into frontend/uploads
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else '.jpg'
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']:
        ext = '.jpg'
    filename = f"prod_{uuid.uuid4().hex[:10]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/uploads/{filename}"}

# --- Database Seeder ---
@app.get("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    # Check if categories exist
    if db.query(models.Category).first():
        return {"message": "Database already seeded"}

    # Seed User & Seller
    user = models.User(
        name="متجر شي لاند الرسمي",
        email="seller@sheland.com",
        password_hash="hashed_secret",
        role="seller"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    seller = models.Seller(user_id=user.id, store_name="Sheland Official Store", rating=4.8)


    db.add(seller)
    db.commit()
    db.refresh(seller)

    # Seed Categories
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

    # Seed Products with Yemeni Rial prices
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

        # Add variants
        v1 = models.ProductVariant(product_id=db_p.id, sku=f"SKU-{db_p.id}-M", color="أسود", size="M", stock=15)
        v2 = models.ProductVariant(product_id=db_p.id, sku=f"SKU-{db_p.id}-L", color="أبيض", size="L", stock=20)
        db.add(v1)
        db.add(v2)
        db.commit()

    # Seed Coupons
    c1 = models.Coupon(code="CITY10", discount_type="percent", discount_value=10.0, min_order_amount=0.0)
    c2 = models.Coupon(code="SAVE20", discount_type="fixed", discount_value=20.0, min_order_amount=50.0)
    c3 = models.Coupon(code="CITY25", discount_type="percent", discount_value=25.0, min_order_amount=100.0)
    db.add(c1)
    db.add(c2)
    db.add(c3)
    db.commit()

    return {"status": "success", "message": "Database seeded with products and coupons!"}

