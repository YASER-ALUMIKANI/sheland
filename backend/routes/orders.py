"""
CityLand Backend - Orders Routes
"""
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth
from backend.main import limiter

router = APIRouter()


@router.get("/api/orders", response_model=List[schemas.OrderResponse])
def get_orders(
    phone: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "super_admin", "sales_manager"]))
):
    """Admin/Sales Manager endpoint to query orders. Protected against unauthorized access."""
    query = db.query(models.Order)
    if user_id:
        query = query.filter(models.Order.user_id == user_id)
    elif phone:
        clean_phone = phone.strip().replace('+', '')
        query = query.filter(
            (models.Order.phone.like(f"%{clean_phone}%")) |
            (models.Order.shipping_address.like(f"%{clean_phone}%"))
        )
    return query.order_by(models.Order.id.desc()).all()


@router.get("/api/orders/my", response_model=List[schemas.OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_current_user)
):
    """Returns all orders belonging to the currently authenticated user by unique user_id."""
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(models.Order.id.desc()).all()


@router.put("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "sales_manager"]))
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return {"status": "success", "order_id": order_id, "new_status": status}


@router.put("/api/orders/{order_id}/parcel-details")
def update_parcel_details(
    order_id: int,
    details: schemas.ParcelDetailsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "sales_manager"]))
):
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


@router.get("/api/orders/track/{order_number}", response_model=schemas.OrderResponse)
def track_order(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_current_user),
):
    order = db.query(models.Order).filter(models.Order.order_number == order_number.upper()).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role not in ("admin", "super_admin", "sales_manager") and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="غير مصرح: ليس لديك صلاحية تتبع هذا الطلب")
    return order


@router.post("/api/orders", response_model=schemas.OrderResponse)
@limiter.limit("30/minute")
def create_order(
    request: Request,
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    """Creates a new order bound to current authenticated user (or guest) securely."""
    effective_user_id = current_user.id if current_user else order_in.user_id

    stock_errors = []

    for item in order_in.items:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"المنتج {item.product_id} غير موجود")
        
        if item.variant_id:
            # ponytail: Use with_for_update for pessimistic row locking to prevent race conditions during concurrent orders
            try:
                variant = db.query(models.ProductVariant).with_for_update().filter(models.ProductVariant.id == item.variant_id).first()
            except Exception:
                variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            available = variant.stock if variant else 0
        else:
            available = prod.stock

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
    pay_method = (order_in.payment_method or "COD").lower()
    pay_status = "pending_delivery" if pay_method in ["cod", "cash"] else ("paid" if order_in.payment_tx_id else "pending_verification")

    db_order = models.Order(
        order_number=order_number,
        user_id=effective_user_id,
        customer_name=order_in.customer_name or (current_user.name if current_user else "عميل شي لاند"),
        phone=order_in.phone or (current_user.phone if current_user else "967770000000"),
        shipping_address=order_in.shipping_address,

        payment_method=order_in.payment_method,
        payment_status=pay_status,
        payment_tx_id=order_in.payment_tx_id,
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

            remaining_to_deduct = item.quantity
            if item.variant_id:
                try:
                    variant = db.query(models.ProductVariant).with_for_update().filter(models.ProductVariant.id == item.variant_id).first()
                except Exception:
                    variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
                if variant:
                    if variant.stock < remaining_to_deduct:
                        db.delete(db_order)
                        db.commit()
                        raise HTTPException(status_code=422, detail="عذراً، نفدت كمية المنتج أثناء معالجة الطلب")
                    variant.stock = max(0, variant.stock - remaining_to_deduct)
            else:
                variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == item.product_id).all()
                for v in variants:
                    if remaining_to_deduct <= 0:
                        break
                    deduct = min(v.stock, remaining_to_deduct)
                    v.stock -= deduct
                    remaining_to_deduct -= deduct

    applied_coupon_code = None
    discount = 0.0

    if order_in.coupon_code:
        code_upper = order_in.coupon_code.strip().upper()
        coupon = db.query(models.Coupon).filter(models.Coupon.code == code_upper, models.Coupon.is_active == True).first()
        if coupon and total >= coupon.min_order_amount:
            applied_coupon_code = coupon.code
            if coupon.discount_type == "percent":
                discount = round(total * (coupon.discount_value / 100.0), 2)
            elif coupon.discount_type == "fixed":
                discount = min(total, coupon.discount_value)

    final_net_total = max(0.0, round(total - discount, 2))

    db_order.coupon_code = applied_coupon_code or (order_in.coupon_code.strip().upper() if order_in.coupon_code else None)
    db_order.discount_amount = round(discount, 2)
    db_order.total_amount = final_net_total
    db.commit()
    db.refresh(db_order)
    return db_order
