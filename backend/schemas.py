from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# -----------------------------------------------------------------------------
# User Schemas
# -----------------------------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password at least 6 characters")
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# -----------------------------------------------------------------------------
# Shipping Address Schemas
# -----------------------------------------------------------------------------
class AddressCreate(BaseModel):
    full_name: str
    phone: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str = "India"
    is_default: bool = False

class AddressResponse(AddressCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# Category Schemas
# -----------------------------------------------------------------------------
class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0

class CategoryResponse(CategoryCreate):
    id: int
    product_count: Optional[int] = 0

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# Product Variant & Image Schemas
# -----------------------------------------------------------------------------
class VariantCreate(BaseModel):
    size: str
    color: str
    stock_quantity: int = Field(ge=0)
    sku: Optional[str] = None

class VariantResponse(VariantCreate):
    id: int
    product_id: int

    class Config:
        from_attributes = True

class ImageCreate(BaseModel):
    image_url: str
    is_primary: bool = False
    display_order: int = 0

class ImageResponse(ImageCreate):
    id: int

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# Review Schemas
# -----------------------------------------------------------------------------
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: str = Field(..., min_length=3)

class ReviewResponse(BaseModel):
    id: int
    user_name: str
    rating: int
    title: Optional[str] = None
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# Product Schemas
# -----------------------------------------------------------------------------
class ProductCreate(BaseModel):
    name: str
    slug: str
    description: str
    material_details: Optional[str] = None
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = None
    category_id: int
    gender: str = "Unisex"
    is_featured: bool = False
    is_trending: bool = False
    is_new_arrival: bool = True
    images: List[ImageCreate] = []
    variants: List[VariantCreate] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    material_details: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    category_id: Optional[int] = None
    gender: Optional[str] = None
    is_featured: Optional[bool] = None
    is_trending: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    is_active: Optional[bool] = None

class ProductStockUpdate(BaseModel):
    variant_id: int
    stock_quantity: int = Field(..., ge=0)

class ProductListItemResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: float
    discount_price: Optional[float] = None
    category_id: int
    category_name: Optional[str] = None
    gender: str
    is_featured: bool
    is_trending: bool
    is_new_arrival: bool
    is_active: bool
    rating: float
    review_count: int
    primary_image: str
    available_sizes: List[str] = []
    available_colors: List[str] = []
    in_stock: bool = True

    class Config:
        from_attributes = True

class ProductDetailResponse(ProductListItemResponse):
    material_details: Optional[str] = None
    images: List[ImageResponse] = []
    variants: List[VariantResponse] = []
    reviews: List[ReviewResponse] = []

# -----------------------------------------------------------------------------
# Coupon Schemas
# -----------------------------------------------------------------------------
class CouponCreate(BaseModel):
    code: str
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    min_purchase: float = 0.0
    max_discount: Optional[float] = None
    is_active: bool = True
    usage_limit: Optional[int] = None
    expires_at: Optional[datetime] = None

class CouponResponse(CouponCreate):
    id: int
    times_used: int
    created_at: datetime

    class Config:
        from_attributes = True

class CouponValidateRequest(BaseModel):
    code: str
    subtotal: float

class CouponValidateResponse(BaseModel):
    valid: bool
    message: str
    code: Optional[str] = None
    discount_amount: float = 0.0

# -----------------------------------------------------------------------------
# Order & Cart Schemas
# -----------------------------------------------------------------------------
class OrderItemCreate(BaseModel):
    product_id: int
    size: str
    color: str
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    shipping_address: str
    city: str
    state: str
    postal_code: str
    country: str = "India"
    payment_method: str = "COD"  # Cash on Delivery
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_items=1)

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    size: str
    color: str
    unit_price: float
    quantity: int
    subtotal: float
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: Optional[int] = None
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    city: str
    state: str
    postal_code: str
    country: str
    payment_method: str
    payment_status: str
    subtotal: float
    discount_amount: float
    shipping_fee: float
    total_amount: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending, Confirmed, Processing, Shipped, Delivered, Cancelled")

# -----------------------------------------------------------------------------
# Admin & Misc Schemas
# -----------------------------------------------------------------------------
class AdminDashboardStats(BaseModel):
    total_sales: float
    total_orders: int
    total_products: int
    total_customers: int
    pending_orders: int
    low_stock_count: int

class NewsletterSubscribe(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str
    success: bool = True
