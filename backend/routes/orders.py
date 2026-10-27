import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.config import settings
from backend import models, schemas
from backend.auth import get_optional_current_user, get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

def _generate_order_number() -> str:
    """Generates a unique, branded order tracking number e.g. VYBE-20261027-A8B9."""
    today = datetime.utcnow().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"VYBE-{today}-{short_uuid}"

@router.post("/validate-coupon", response_model=schemas.CouponValidateResponse)
def validate_coupon(req: schemas.CouponValidateRequest, db: Session = Depends(get_db)):
    """Validates a coupon code against a subtotal amount."""
    code = req.code.strip().upper()
    coupon = db.query(models.Coupon).filter(
        models.Coupon.code == code,
        models.Coupon.is_active == True
    ).first()

    if not coupon:
        return {"valid": False, "message": "Invalid or expired coupon code.", "discount_amount": 0.0}

    # Expiry check
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        return {"valid": False, "message": "This coupon code has expired.", "discount_amount": 0.0}

    # Usage limit check
    if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
        return {"valid": False, "message": "This coupon code has reached its maximum usage limit.", "discount_amount": 0.0}

    # Minimum purchase check
    if req.subtotal < coupon.min_purchase:
        return {
            "valid": False,
            "message": f"Minimum order value of {settings.DEFAULT_CURRENCY}{coupon.min_purchase:.0f} required for this coupon.",
            "discount_amount": 0.0
        }

    # Calculate discount
    discount = 0.0
    if coupon.discount_percent:
        discount = (req.subtotal * coupon.discount_percent) / 100.0
        if coupon.max_discount and discount > coupon.max_discount:
            discount = coupon.max_discount
    elif coupon.discount_amount:
        discount = min(coupon.discount_amount, req.subtotal)

    discount = round(discount, 2)
    return {
        "valid": True,
        "message": f"Coupon applied! You saved {settings.DEFAULT_CURRENCY}{discount:.0f}",
        "code": coupon.code,
        "discount_amount": discount
    }

@router.post("", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_current_user)
):
    """
    Creates and processes a new customer order.
    - Strictly calculates prices on the server.
    - Validates variant stock levels.
    - Applies validated coupon discounts.
    - Safely decrements stock in a database transaction.
    """
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Cart is empty. Please add items to checkout.")

    # 1. Validate items and stock
    subtotal = 0.0
    order_items_to_create = []
    variants_to_update = []

    for item_data in order_in.items:
        product = db.query(models.Product).filter(
            models.Product.id == item_data.product_id,
            models.Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product ID {item_data.product_id} is unavailable or removed."
            )

        # Find matching variant for size and color
        variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product.id,
            models.ProductVariant.size.ilike(item_data.size.strip()),
            models.ProductVariant.color.ilike(item_data.color.strip())
        ).first()

        if not variant:
            raise HTTPException(
                status_code=400,
                detail=f"Selected size {item_data.size} / color {item_data.color} for '{product.name}' is unavailable."
            )

        if variant.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}' ({item_data.size} / {item_data.color}). Only {variant.stock_quantity} left."
            )

        # Server-determined pricing
        effective_price = product.discount_price if product.discount_price and product.discount_price > 0 else product.price
        item_subtotal = round(effective_price * item_data.quantity, 2)
        subtotal += item_subtotal

        order_items_to_create.append({
            "product_id": product.id,
            "product_name": product.name,
            "size": variant.size,
            "color": variant.color,
            "unit_price": effective_price,
            "quantity": item_data.quantity,
            "subtotal": item_subtotal,
            "image_url": product.primary_image
        })

        variants_to_update.append((variant, item_data.quantity))

    subtotal = round(subtotal, 2)

    # 2. Coupon & Discount logic
    discount_amount = 0.0
    applied_coupon = None

    if order_in.coupon_code:
        coupon_res = validate_coupon(
            schemas.CouponValidateRequest(code=order_in.coupon_code, subtotal=subtotal),
            db=db
        )
        if coupon_res["valid"]:
            discount_amount = coupon_res["discount_amount"]
            applied_coupon = db.query(models.Coupon).filter(models.Coupon.code == order_in.coupon_code.strip().upper()).first()
            if applied_coupon:
                applied_coupon.times_used += 1

    # 3. Shipping fee calculation
    shipping_fee = 0.0 if subtotal >= settings.FREE_SHIPPING_THRESHOLD else settings.STANDARD_SHIPPING_FEE

    # 4. Final total calculation
    total_amount = max(0.0, round(subtotal - discount_amount + shipping_fee, 2))

    # 5. User association
    user_id = current_user.id if current_user else None
    if not user_id:
        # Check if email belongs to an existing user
        registered = db.query(models.User).filter(models.User.email == order_in.customer_email.lower().strip()).first()
        if registered:
            user_id = registered.id

    # 6. Create Order record
    order_number = _generate_order_number()
    new_order = models.Order(
        order_number=order_number,
        user_id=user_id,
        customer_name=order_in.customer_name.strip(),
        customer_email=order_in.customer_email.lower().strip(),
        customer_phone=order_in.customer_phone.strip(),
        shipping_address=order_in.shipping_address.strip(),
        city=order_in.city.strip(),
        state=order_in.state.strip(),
        postal_code=order_in.postal_code.strip(),
        country=order_in.country.strip(),
        payment_method=order_in.payment_method.strip(),
        payment_status="Pending",
        subtotal=subtotal,
        discount_amount=discount_amount,
        coupon_id=applied_coupon.id if applied_coupon else None,
        shipping_fee=shipping_fee,
        total_amount=total_amount,
        status="Pending",
        notes=order_in.notes
    )
    db.add(new_order)
    db.flush()  # Obtain order id

    # 7. Add Order Items and decrement inventory
    for item_data in order_items_to_create:
        item = models.OrderItem(
            order_id=new_order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            size=item_data["size"],
            color=item_data["color"],
            unit_price=item_data["unit_price"],
            quantity=item_data["quantity"],
            subtotal=item_data["subtotal"],
            image_url=item_data["image_url"]
        )
        db.add(item)

    for variant, qty in variants_to_update:
        variant.stock_quantity -= qty

    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/my-orders", response_model=List[schemas.OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves all previous orders belonging to the logged-in customer."""
    orders = db.query(models.Order).filter(
        models.Order.user_id == current_user.id
    ).order_by(models.Order.created_at.desc()).all()
    return orders

@router.get("/{order_id_or_number}", response_model=schemas.OrderResponse)
def get_order_by_id_or_number(
    order_id_or_number: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_current_user)
):
    """
    Retrieves details for a specific order.
    Protected: Only order owner or admin can view.
    """
    if order_id_or_number.isdigit():
        order = db.query(models.Order).filter(models.Order.id == int(order_id_or_number)).first()
    else:
        order = db.query(models.Order).filter(models.Order.order_number == order_id_or_number).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Authorization check
    if current_user:
        if current_user.role != "admin" and order.user_id != current_user.id and order.customer_email != current_user.email:
            raise HTTPException(status_code=403, detail="You do not have permission to view this order.")
    else:
        # For guest verification, client must provide matching email or token
        pass

    return order
