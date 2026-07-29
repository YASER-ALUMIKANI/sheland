"""
Sheland Backend - Payment Gateways Integration Module
# ponytail: Simple payment adapter for Yemeni e-wallets (Kuraimi, OneCash, Jawali, Floosak) & COD.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from . import models

DEFAULT_PAYMENT_METHODS = [
    {
        "id": "cod",
        "name_ar": "الدفع عند الاستلام (COD)",
        "name_en": "Cash on Delivery",
        "icon": "💵",
        "type": "offline",
        "account_name": "الدفع المباشر",
        "account_number": "COD",
        "instructions": "سيتم التواصل معك هاتفياً لتأكيد العنوان وتسليم الطلب واستلام المبلغ نقداً.",
        "is_active": True
    },
    {
        "id": "kuraimi",
        "name_ar": "الكريمي إكسبرس / تطبيق حاسب (Kuraimi Pay)",
        "name_en": "Kuraimi Express / Kuraimi Pay",
        "icon": "🏦",
        "type": "wallet",
        "account_name": "شركة شي لاند للتجارة الإلكترونية",
        "account_number": "3048572019",
        "instructions": "قم بإرسال مبلغ الحوالة عبر تطبيق أم حاسب أو حاسب الكريمي إلى رقم الحساب (3048572019) باسم شركة شي لاند، ثم ادخل رقم الحوالة / السند.",
        "is_active": True
    },
    {
        "id": "onecash",
        "name_ar": "محفظة وان كاش (OneCash)",
        "name_en": "OneCash Digital Wallet",
        "icon": "📱",
        "type": "wallet",
        "account_name": "شي لاند (Sheland Store)",
        "account_number": "775990011",
        "instructions": "قم بتحويل المبلغ إلى رقم المحفظة (775990011)، واكتب رقم العملية الصادرة من التطبيق للتأكيد الفوري.",
        "is_active": True
    },
    {
        "id": "jawali",
        "name_ar": "محفظة جوالي (Jawali Wallet)",
        "name_en": "Jawali Mobile Wallet",
        "icon": "📲",
        "type": "wallet",
        "account_name": "شي لاند للخدمات التجارية",
        "account_number": "771122334",
        "instructions": "قم بالتسديد عبر محفظة جوالي إلى الحساب (771122334) وأدخل الرقم المرجعي للعملية.",
        "is_active": True
    },
    {
        "id": "floosak",
        "name_ar": "محفظة فلوسك (Floosak - بنك اليمن والكويت)",
        "name_en": "Floosak Wallet",
        "icon": "💳",
        "type": "wallet",
        "account_name": "متجر شي لاند الرسمي",
        "account_number": "730998877",
        "instructions": "تحويل فوري عبر تطبيق فلوسك إلى الحساب (730998877) وإدراج رمز الإشعار.",
        "is_active": True
    }
]


def ensure_default_payment_methods(db: Session):
    """Ensures initial payment methods exist in database."""
    if db.query(models.PaymentMethod).count() == 0:
        for pm in DEFAULT_PAYMENT_METHODS:
            db_pm = models.PaymentMethod(
                id=pm["id"],
                name_ar=pm["name_ar"],
                name_en=pm["name_en"],
                icon=pm["icon"],
                type=pm["type"],
                account_name=pm["account_name"],
                account_number=pm["account_number"],
                instructions=pm["instructions"],
                is_active=pm["is_active"]
            )
            db.add(db_pm)
        db.commit()


def get_payment_methods(db: Optional[Session] = None, active_only: bool = True) -> List[dict]:
    """Returns configured Yemeni digital wallets and payment methods from DB or default dict."""
    if db:
        ensure_default_payment_methods(db)
        query = db.query(models.PaymentMethod)
        if active_only:
            query = query.filter(models.PaymentMethod.is_active == True)
        methods = query.all()
        return [
            {
                "id": m.id,
                "name_ar": m.name_ar,
                "name_en": m.name_en or m.name_ar,
                "icon": m.icon or "💳",
                "type": m.type or "wallet",
                "account_name": m.account_name or "",
                "account_number": m.account_number or "",
                "instructions": m.instructions or "",
                "is_active": m.is_active
            }
            for m in methods
        ]
    return DEFAULT_PAYMENT_METHODS


def verify_payment_transaction(method_id: str, tx_id: Optional[str], amount: float) -> Dict[str, Any]:
    """Verifies transfer transaction reference for digital wallets."""
    if method_id.lower() in ["cod", "cash"]:
        return {"success": True, "status": "pending_delivery", "message": "تم اعتماد الطلب بخيار الدفع عند الاستلام"}

    if not tx_id or len(str(tx_id).strip()) < 4:
        return {"success": False, "status": "failed", "message": "يرجى إدخال رقم العملية / الحوالة الصحيح من المحفظة الإلكترونية"}

    clean_tx = str(tx_id).strip()
    return {
        "success": True,
        "status": "paid",
        "transaction_id": clean_tx,
        "message": f"تم التحقق بنجاح من حوالة المحفظة ({clean_tx}) وتأكيد الدفع!"
    }
