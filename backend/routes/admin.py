from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from backend.database import get_db
from backend import models, schemas
from backend.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

@router.get("/dashboard", response_model=schemas.AdminDashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Returns core business KPIs for the admin dashboard.
    """
    # Total sales from non-cancelled orders
    total_sales = db.query(func.coalesce(func.sum(models.Order.total_amount), 0.0)).filter(
        models.Order.status != "Cancelled"
    ).scalar()

    total_orders = db.query(models.Order).count()
    pending_orders = db.query(models.Order).filter(models.Order.status == "Pending").count()
    total_products = db.query(models.Product).filter(models.Product.is_active == True).count()
    total_customers = db.query(models.User).filter(models.User.role == "customer").count()

    # Low stock variants (< 5)
    low_stock_count = db.query(models.ProductVariant).filter(
        models.ProductVariant.stock_quantity <= 5
    ).count()

    return {
        "total_sales": round(total_sales, 2),
        "total_orders": total_orders,
        "total_products": total_products,
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "low_stock_count": low_stock_count
    }

@router.get("/orders", response_model=List[schemas.OrderResponse])
def get_all_orders(
    status_filter: Optional[str] = Query(None, description="Pending, Confirmed, Processing, Shipped, Delivered, Cancelled"),
    search: Optional[str] = Query(None, description="Search by order number, customer name, email, or phone"),
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Admin endpoint to view and filter customer orders."""
    query = db.query(models.Order)

    if status_filter:
        query = query.filter(models.Order.status == status_filter)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Order.order_number.ilike(s),
                models.Order.customer_name.ilike(s),
                models.Order.customer_email.ilike(s),
                models.Order.customer_phone.ilike(s)
            )
        )

    orders = query.order_by(desc(models.Order.created_at)).offset(skip).limit(limit).all()
    return orders

@router.patch("/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: int,
    status_data: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Updates the fulfillment status of an order.
    If changed to 'Cancelled', automatically restocks the product items.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    valid_statuses = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
    new_status = status_data.status.strip().capitalize()
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status_data.status}'. Must be one of: {', '.join(valid_statuses)}"
        )

    old_status = order.status

    # If cancelling an active order, restock the inventory
    if new_status == "Cancelled" and old_status != "Cancelled":
        for item in order.items:
            variant = db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id == item.product_id,
                models.ProductVariant.size.ilike(item.size),
                models.ProductVariant.color.ilike(item.color)
            ).first()
            if variant:
                variant.stock_quantity += item.quantity

    # If un-cancelling a previously cancelled order, re-deduct if stock available
    elif old_status == "Cancelled" and new_status != "Cancelled":
        for item in order.items:
            variant = db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id == item.product_id,
                models.ProductVariant.size.ilike(item.size),
                models.ProductVariant.color.ilike(item.color)
            ).first()
            if variant:
                variant.stock_quantity = max(0, variant.stock_quantity - item.quantity)

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order

@router.get("/low-stock")
def get_low_stock_products(
    threshold: int = Query(5, ge=0),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Lists all product variants whose inventory is below or equal to the threshold."""
    variants = db.query(models.ProductVariant).join(models.Product).filter(
        models.Product.is_active == True,
        models.ProductVariant.stock_quantity <= threshold
    ).all()

    return [
        {
            "variant_id": v.id,
            "product_id": v.product_id,
            "product_name": v.product.name,
            "sku": v.sku,
            "size": v.size,
            "color": v.color,
            "stock_quantity": v.stock_quantity,
            "primary_image": v.product.primary_image
        }
        for v in variants
    ]

# -----------------------------------------------------------------------------
# Coupon Management
# -----------------------------------------------------------------------------
@router.get("/coupons", response_model=List[schemas.CouponResponse])
def list_coupons(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Lists all active and inactive promotional coupons."""
    return db.query(models.Coupon).order_by(desc(models.Coupon.created_at)).all()

@router.post("/coupons", response_model=schemas.CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon_in: schemas.CouponCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Creates a new discount coupon."""
    code = coupon_in.code.strip().upper()
    existing = db.query(models.Coupon).filter(models.Coupon.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="A coupon with this code already exists.")

    new_coupon = models.Coupon(
        code=code,
        discount_percent=coupon_in.discount_percent,
        discount_amount=coupon_in.discount_amount,
        min_purchase=coupon_in.min_purchase,
        max_discount=coupon_in.max_discount,
        is_active=coupon_in.is_active,
        usage_limit=coupon_in.usage_limit,
        expires_at=coupon_in.expires_at
    )
    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return new_coupon

@router.delete("/coupons/{coupon_id}", response_model=schemas.MessageResponse)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Deletes or deactivates a coupon."""
    coupon = db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found.")
    db.delete(coupon)
    db.commit()
    return {"message": f"Coupon '{coupon.code}' deleted.", "success": True}

@router.get("/customers")
def list_customers(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Returns list of registered customers with total order spend."""
    users = db.query(models.User).filter(models.User.role == "customer").order_by(desc(models.User.created_at)).all()
    results = []
    for u in users:
        order_count = len(u.orders)
        total_spend = sum(o.total_amount for o in u.orders if o.status != "Cancelled")
        results.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "created_at": u.created_at,
            "order_count": order_count,
            "total_spend": round(total_spend, 2)
        })
    return results
