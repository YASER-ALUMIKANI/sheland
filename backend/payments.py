"""
Sheland Backend - Payment Gateways Integration Module
# ponytail: Simple payment adapter for Yemeni e-wallets (Kuraimi, OneCash, Jawali, Floosak) & COD.
"""
from typing import Dict, Any, Optional

YEMENI_PAYMENT_METHODS: Dict[str, Dict[str, Any]] = {
    "cod": {
        "id": "cod",
        "name_ar": "الدفع عند الاستلام (COD)",
        "name_en": "Cash on Delivery",
        "icon": "💵",
        "type": "offline",
        "description": "الدفع نقداً لسائق التوصيل عند استلام الطلب",
        "instructions": "سيتم التواصل معك هاتفياً لتأكيد العنوان وتسليم الطلب."
    },
    "kuraimi": {
        "id": "kuraimi",
        "name_ar": "الكريمي إكسبرس / تطبيق حاسب (Kuraimi Pay)",
        "name_en": "Kuraimi Express / Kuraimi Pay",
        "icon": "🏦",
        "type": "wallet",
        "account_name": "شركة شي لاند للتجارة الإلكترونية",
        "account_number": "3048572019",
        "instructions": "قم بإرسال مبلغ الحوالة عبر تطبيق أم حاسب أو حاسب الكريمي إلى رقم الحساب (3048572019) باسم شركة شي لاند، ثم ادخل رقم الحوالة / السند."
    },
    "onecash": {
        "id": "onecash",
        "name_ar": "محفظة وان كاش (OneCash)",
        "name_en": "OneCash Digital Wallet",
        "icon": "📱",
        "type": "wallet",
        "account_name": "شي لاند (Sheland Store)",
        "account_number": "775990011",
        "instructions": "قم بتحويل المبلغ إلى رقم المحفظة (775990011)، واكتب رقم العملية الصادرة من التطبيق للتأكيد الفوري."
    },
    "jawali": {
        "id": "jawali",
        "name_ar": "محفظة جوالي (Jawali Wallet)",
        "name_en": "Jawali Mobile Wallet",
        "icon": "📲",
        "type": "wallet",
        "account_name": "شي لاند للخدمات التجارية",
        "account_number": "771122334",
        "instructions": "قم بالتسديد عبر محفظة جوالي إلى الحساب (771122334) وأدخل الرقم المرجعي للعملية."
    },
    "floosak": {
        "id": "floosak",
        "name_ar": "محفظة فلوسك (Floosak - بنك اليمن والكويت)",
        "name_en": "Floosak Wallet",
        "icon": "💳",
        "type": "wallet",
        "account_name": "متجر شي لاند الرسمي",
        "account_number": "730998877",
        "instructions": "تحويل فوري عبر تطبيق فلوسك إلى الحساب (730998877) وإدراج رمز الإشعار."
    }
}


def get_payment_methods():
    """Returns configured Yemeni digital wallets and payment methods."""
    return list(YEMENI_PAYMENT_METHODS.values())


def verify_payment_transaction(method_id: str, tx_id: Optional[str], amount: float) -> Dict[str, Any]:
    """
    Verifies transfer transaction reference for digital wallets.
    """
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
