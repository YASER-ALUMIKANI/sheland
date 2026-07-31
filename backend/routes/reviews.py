"""
CityLand Backend - Reviews Routes
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth
from backend.main import limiter, validate_and_save_image

router = APIRouter()


@router.get("/api/products/{product_id}/reviews", response_model=List[schemas.ReviewResponse])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.Review).filter(models.Review.product_id == product_id).order_by(models.Review.id.desc()).all()


@router.post("/api/reviews/upload-photo")
@limiter.limit("10/minute")
async def upload_review_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.require_current_user)
):
    """Authenticated endpoint for registered customers to upload a review photo with rate limiting & strict validation."""
    contents = await file.read()
    url = validate_and_save_image(contents, prefix="review")
    return {"url": url}


@router.get("/api/orders/check-purchased")
def check_order_purchased(
    order_number: str = Query(...),
    product_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Verifies that a given order_number contains the product, returning customer name for review pre-fill."""
    order = db.query(models.Order).filter(models.Order.order_number == order_number.upper()).first()
    if not order:
        raise HTTPException(status_code=404, detail="رقم الطلب غير موجود")
    purchased = any(item.product_id == product_id for item in order.items)
    return {
        "verified": purchased,
        "customer_name": order.customer_name if purchased else None
    }


@router.post("/api/products/{product_id}/reviews", response_model=schemas.ReviewResponse)
def create_product_review(
    product_id: int,
    review_in: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_current_user)
):
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    delivered_statuses = ["delivered", "مكتمل", "completed", "تم التسليم", "مكتمل (تم التسليم)"]
    delivered_order = (
        db.query(models.Order)
        .join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
        .filter(
            models.Order.user_id == current_user.id,
            models.Order.status.in_(delivered_statuses),
            models.OrderItem.product_id == product_id
        )
        .order_by(models.Order.id.desc())
        .first()
    )

    if not delivered_order:
        any_order = (
            db.query(models.Order)
            .join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
            .filter(
                models.Order.user_id == current_user.id,
                models.OrderItem.product_id == product_id
            )
            .first()
        )
        if any_order:
            raise HTTPException(
                status_code=400,
                detail="يمكنك إضافة تقييمك بعد استلام الطلب وتغيير حالته إلى مكتمل (delivered)"
            )
        else:
            raise HTTPException(
                status_code=403,
                detail="عذراً، يمكنك إضافة تقييم فقط للمنتجات التي قمت بشرائها واستلامها بنجاح"
            )

    db_review = models.Review(
        product_id=product_id,
        user_id=current_user.id,
        author_name=current_user.name or review_in.author_name or "عميل شي لاند",
        order_number=delivered_order.order_number,
        is_verified_purchase=True,
        rating=review_in.rating,
        comment=review_in.comment,
        image_url=review_in.image_url
    )
    db.add(db_review)

    all_revs = db.query(models.Review).filter(models.Review.product_id == product_id).all()
    ratings_list = [r.rating for r in all_revs] + [review_in.rating]
    prod.rating = round(sum(ratings_list) / len(ratings_list), 1)
    prod.review_count = len(ratings_list)

    db.commit()
    db.refresh(db_review)
    return db_review
