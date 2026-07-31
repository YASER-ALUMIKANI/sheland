"""
CityLand Backend - Payment Methods Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth, payments

router = APIRouter()


@router.get("/api/payments/methods")
def get_payment_methods(db: Session = Depends(get_db)):
    """Returns list of active payment methods and Yemeni digital wallets for checkout."""
    return payments.get_payment_methods(db, active_only=True)


@router.get("/api/admin/payments")
def get_admin_payment_methods(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "super_admin"]))
):
    """Returns all payment methods including inactive ones for Admin management."""
    return payments.get_payment_methods(db, active_only=False)


@router.post("/api/admin/payments", response_model=schemas.PaymentMethodResponse)
def create_payment_method(
    pm_in: schemas.PaymentMethodBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "super_admin"]))
):
    """Creates a new payment gateway or digital wallet."""
    existing = db.query(models.PaymentMethod).filter(models.PaymentMethod.id == pm_in.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="طريقة الدفع أو المحفظة موجودة بالفعل")

    db_pm = models.PaymentMethod(**pm_in.dict())
    db.add(db_pm)
    db.commit()
    db.refresh(db_pm)
    return db_pm


@router.put("/api/admin/payments/{method_id}", response_model=schemas.PaymentMethodResponse)
def update_payment_method(
    method_id: str,
    pm_in: schemas.PaymentMethodBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "super_admin"]))
):
    """Updates account numbers, instructions, names, or active status of payment method."""
    db_pm = db.query(models.PaymentMethod).filter(models.PaymentMethod.id == method_id).first()
    if not db_pm:
        raise HTTPException(status_code=404, detail="طريقة الدفع غير موجودة")

    for field, val in pm_in.dict(exclude_unset=True).items():
        setattr(db_pm, field, val)

    db.commit()
    db.refresh(db_pm)
    return db_pm


@router.delete("/api/admin/payments/{method_id}")
def delete_payment_method(
    method_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "super_admin"]))
):
    """Deletes a payment method from database."""
    db_pm = db.query(models.PaymentMethod).filter(models.PaymentMethod.id == method_id).first()
    if not db_pm:
        raise HTTPException(status_code=404, detail="طريقة الدفع غير موجودة")

    db.delete(db_pm)
    db.commit()
    return {"status": "success", "message": f"تم حذف طريقة الدفع {method_id} بنجاح"}


@router.put("/api/admin/orders/{order_id}/verify-payment")
def verify_admin_order_payment(
    order_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["admin", "sales_manager"]))
):
    """Admin endpoint to approve, verify or update payment status of an order."""
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    new_status = payload.get("payment_status", "paid")
    db_order.payment_status = new_status
    if payload.get("payment_tx_id"):
        db_order.payment_tx_id = payload.get("payment_tx_id")

    db.commit()
    db.refresh(db_order)
    return {"status": "success", "order_id": order_id, "payment_status": db_order.payment_status, "payment_tx_id": db_order.payment_tx_id}


@router.post("/api/payments/verify")
def verify_payment(payload: dict):
    """Verifies transaction reference code for digital wallet payments."""
    method = payload.get("method", "cod")
    tx_id = payload.get("tx_id")
    amount = float(payload.get("amount", 0))
    return payments.verify_payment_transaction(method, tx_id, amount)
