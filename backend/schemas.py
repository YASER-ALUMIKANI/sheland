"""
CityLand Backend - Pydantic Validation Schemas
# ponytail: Strict validation using standard Pydantic models for safety
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# ==========================================================================
# Auth Schemas
# ==========================================================================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None
    role: Optional[str] = "customer"  # customer, seller, admin

class UserLogin(BaseModel):
    email_or_phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryBase(BaseModel):
    name_ar: str
    name_en: str
    slug: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class VariantBase(BaseModel):
    sku: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    stock: int = Field(default=10, ge=0)
    price_override: Optional[float] = None

class VariantResponse(VariantBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    title_ar: str = Field(..., min_length=2, max_length=200)
    title_en: str = Field(..., min_length=2, max_length=200)
    slug: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    compare_at_price: Optional[float] = None
    cost_price: Optional[float] = 0.0
    currency: str = "YER"
    image_url: str
    category_id: int

    seller_id: int = 1
    stock: Optional[int] = 10
    free_shipping: bool = True
    cod_available: bool = True


class ProductCreate(ProductBase):
    variants: Optional[List[VariantBase]] = []

class ProductResponse(ProductBase):
    id: int
    rating: float
    review_count: int
    is_featured: bool
    stock: int = 0
    variants: List[VariantResponse] = []

    @classmethod
    def from_orm_with_stock(cls, product):
        # ponytail: compute stock from variants, bypassing Pydantic's ProductBase.stock default
        d = {c.key: getattr(product, c.key) for c in product.__table__.columns}
        d['stock'] = sum(v.stock for v in product.variants) if product.variants else 0
        d['variants'] = [VariantResponse.model_validate(v) for v in product.variants]
        d['rating'] = product.rating
        d['review_count'] = product.review_count
        d['is_featured'] = product.is_featured
        return cls.model_validate(d)

    class Config:
        from_attributes = True

class CartItemCreate(BaseModel):
    user_id: int = 1
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)

class OrderCreate(BaseModel):
    user_id: Optional[int] = None
    customer_name: Optional[str] = "عميل شي لاند"
    phone: Optional[str] = None
    shipping_address: str
    payment_method: str = "COD"
    payment_tx_id: Optional[str] = None
    items: List[CartItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    price: float
    quantity: int
    product_title: Optional[str] = "منتج من منصة شي لاند"

    class Config:
        from_attributes = True

class ParcelDetailsUpdate(BaseModel):
    parcel_count: Optional[str] = "1 من 1"
    weight: Optional[str] = "0.85 كجم"
    dimensions: Optional[str] = "25 × 15 × 10 سم"

class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: Optional[int] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    shipping_address: str
    payment_method: str
    payment_status: Optional[str] = "pending"
    payment_tx_id: Optional[str] = None
    status: str
    total_amount: float
    parcel_count: Optional[str] = "1 من 1"
    weight: Optional[str] = "0.85 كجم"
    dimensions: Optional[str] = "25 × 15 × 10 سم"
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True



class ReviewCreate(BaseModel):
    author_name: Optional[str] = "عميل شي لاند"

    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=2)

class ReviewResponse(BaseModel):
    id: int
    author_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CouponCreate(BaseModel):
    code: str
    discount_type: str = "percent"
    discount_value: float
    min_order_amount: float = 0.0

class CouponResponse(CouponCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class PaymentMethodBase(BaseModel):
    id: str
    name_ar: str
    name_en: Optional[str] = None
    icon: Optional[str] = "💳"
    type: Optional[str] = "wallet"
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = True

class PaymentMethodResponse(PaymentMethodBase):
    class Config:
        from_attributes = True

