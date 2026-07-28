"""
CityLand Backend - Database Models
# ponytail: Consolidate models into a single readable file for low overhead
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="customer")  # customer, seller, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    seller_profile = relationship("Seller", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    rating = Column(Float, default=4.5)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    children = relationship("Category", backref="parent", remote_side=[id])
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title_ar = Column(String, nullable=False)
    title_en = Column(String, nullable=False)
    slug = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)
    currency = Column(String, default="YER")
    image_url = Column(String, nullable=False)

    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    free_shipping = Column(Boolean, default=True)
    cod_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    seller = relationship("Seller", back_populates="products")
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    @property
    def stock(self):
        # ponytail: aggregate total stock across all variants for quick frontend display
        if self.variants:
            return sum(v.stock for v in self.variants)
        return 0

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String, nullable=True)
    color = Column(String, nullable=True)
    size = Column(String, nullable=True)
    stock = Column(Integer, default=10)
    price_override = Column(Float, nullable=True)

    product = relationship("Product", back_populates="variants")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    quantity = Column(Integer, default=1)

    product = relationship("Product")
    variant = relationship("ProductVariant")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, processing, shipped, delivered
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(Text, nullable=False)
    payment_method = Column(String, nullable=False)
    payment_status = Column(String, default="paid")
    # ponytail: Dynamic shipping parcel attributes configurable by order department staff
    parcel_count = Column(String, default="1 من 1")
    weight = Column(String, default="0.85 كجم")
    dimensions = Column(String, default="25 × 15 × 10 سم")
    created_at = Column(DateTime, default=datetime.utcnow)


    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    @property
    def product_title(self):
        return self.product.title_ar if self.product else "منتج شي لاند"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String, default="عميل شي لاند")

    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, default="percent")  # percent, fixed
    discount_value = Column(Float, nullable=False)
    min_order_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

