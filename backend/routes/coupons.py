"""
CityLand Backend - Coupons Routes
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()


@router.get("/api/coupons", response_model=List[schemas.CouponResponse])
def get_coupons(db: Session = Depends(get_db)):
    return db.query(models.Coupon).all()


@router.get("/api/coupons/validate")
@router.post("/api/coupons/validate")
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


@router.post("/api/coupons", response_model=schemas.CouponResponse, status_code=201)
def create_coupon(
    coupon_in: schemas.CouponCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "sales_manager"]))
):
    code_upper = coupon_in.code.strip().upper()
    existing = db.query(models.Coupon).filter(models.Coupon.code == code_upper).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"رمز الكوبون '{code_upper}' موجود مسبقاً.")
    coupon = models.Coupon(
        code=code_upper,
        discount_type=coupon_in.discount_type,
        discount_value=coupon_in.discount_value,
        min_order_amount=coupon_in.min_order_amount,
        is_active=True
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/api/coupons/{coupon_id}", status_code=204)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin"]))
):
    coupon = db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="الكوبون غير موجود.")
    db.delete(coupon)
    db.commit()
