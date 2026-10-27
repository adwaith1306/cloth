from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from backend.database import get_db
from backend import models, schemas
from backend.auth import get_current_admin, get_optional_current_user

router = APIRouter(prefix="/products", tags=["Products"])

def _format_product_list_item(product: models.Product) -> dict:
    """Helper to convert product model into rich list item representation."""
    sizes = list(dict.fromkeys([v.size for v in product.variants if v.stock_quantity > 0]))
    colors = list(dict.fromkeys([v.color for v in product.variants if v.stock_quantity > 0]))
    total_stock = sum(v.stock_quantity for v in product.variants)

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "discount_price": product.discount_price,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
        "gender": product.gender,
        "is_featured": product.is_featured,
        "is_trending": product.is_trending,
        "is_new_arrival": product.is_new_arrival,
        "is_active": product.is_active,
        "rating": product.rating,
        "review_count": product.review_count,
        "primary_image": product.primary_image,
        "available_sizes": sizes,
        "available_colors": colors,
        "in_stock": total_stock > 0
    }

@router.get("", response_model=List[schemas.ProductListItemResponse])
def get_products(
    q: Optional[str] = Query(None, description="Search keyword in name or description"),
    category: Optional[str] = Query(None, description="Category slug or name"),
    gender: Optional[str] = Query(None, description="Men, Women, or Unisex"),
    size: Optional[str] = Query(None, description="Filter by size e.g. M, L, XL"),
    color: Optional[str] = Query(None, description="Filter by color e.g. Black"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    is_featured: Optional[bool] = None,
    is_trending: Optional[bool] = None,
    is_new_arrival: Optional[bool] = None,
    sort_by: Optional[str] = Query("newest", description="newest, price_asc, price_desc, rating, popular"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieves filtered and sorted products with stock status and images.
    """
    query = db.query(models.Product).filter(models.Product.is_active == True)

    if q:
        search_filter = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(search_filter),
                models.Product.description.ilike(search_filter),
                models.Product.material_details.ilike(search_filter)
            )
        )

    if category:
        # Check if category is slug or id
        if category.isdigit():
            query = query.filter(models.Product.category_id == int(category))
        else:
            cat = db.query(models.Category).filter(models.Category.slug == category.lower().strip()).first()
            if cat:
                query = query.filter(models.Product.category_id == cat.id)
            else:
                return []

    if gender:
        query = query.filter(or_(models.Product.gender == gender, models.Product.gender == "Unisex"))

    if is_featured is not None:
        query = query.filter(models.Product.is_featured == is_featured)

    if is_trending is not None:
        query = query.filter(models.Product.is_trending == is_trending)

    if is_new_arrival is not None:
        query = query.filter(models.Product.is_new_arrival == is_new_arrival)

    if min_price is not None:
        query = query.filter(
            or_(
                and_(models.Product.discount_price.isnot(None), models.Product.discount_price >= min_price),
                and_(models.Product.discount_price.is_(None), models.Product.price >= min_price)
            )
        )

    if max_price is not None:
        query = query.filter(
            or_(
                and_(models.Product.discount_price.isnot(None), models.Product.discount_price <= max_price),
                and_(models.Product.discount_price.is_(None), models.Product.price <= max_price)
            )
        )

    if size or color:
        query = query.join(models.Product.variants)
        if size:
            query = query.filter(models.ProductVariant.size.ilike(size.strip()), models.ProductVariant.stock_quantity > 0)
        if color:
            query = query.filter(models.ProductVariant.color.ilike(color.strip()), models.ProductVariant.stock_quantity > 0)
        query = query.distinct()

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(models.Product.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(models.Product.price))
    elif sort_by == "rating":
        query = query.order_by(desc(models.Product.rating), desc(models.Product.review_count))
    elif sort_by == "popular":
        query = query.order_by(desc(models.Product.review_count))
    else:  # newest
        query = query.order_by(desc(models.Product.created_at))

    products = query.offset(skip).limit(limit).all()
    return [_format_product_list_item(p) for p in products]

@router.get("/featured", response_model=List[schemas.ProductListItemResponse])
def get_featured_products(limit: int = 8, db: Session = Depends(get_db)):
    """Returns top featured products for homepage."""
    products = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.is_featured == True
    ).limit(limit).all()
    return [_format_product_list_item(p) for p in products]

@router.get("/trending", response_model=List[schemas.ProductListItemResponse])
def get_trending_products(limit: int = 8, db: Session = Depends(get_db)):
    """Returns trending streetwear items."""
    products = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.is_trending == True
    ).limit(limit).all()
    return [_format_product_list_item(p) for p in products]

@router.get("/new-arrivals", response_model=List[schemas.ProductListItemResponse])
def get_new_arrivals(limit: int = 8, db: Session = Depends(get_db)):
    """Returns freshest new drops."""
    products = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.is_new_arrival == True
    ).order_by(desc(models.Product.created_at)).limit(limit).all()
    return [_format_product_list_item(p) for p in products]

@router.get("/{id_or_slug}", response_model=schemas.ProductDetailResponse)
def get_product_detail(id_or_slug: str, db: Session = Depends(get_db)):
    """
    Returns single product details by ID or Slug, including images, variants, stock, and reviews.
    """
    if id_or_slug.isdigit():
        product = db.query(models.Product).filter(models.Product.id == int(id_or_slug)).first()
    else:
        product = db.query(models.Product).filter(models.Product.slug == id_or_slug).first()

    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found.")

    formatted = _format_product_list_item(product)
    formatted.update({
        "material_details": product.material_details,
        "images": product.images,
        "variants": product.variants,
        "reviews": product.reviews
    })
    return formatted

@router.post("/{product_id}/reviews", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
def add_product_review(
    product_id: int,
    review_in: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_current_user)
):
    """Submits a customer review and updates the product rating average."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    user_name = current_user.full_name if current_user else "Verified Customer"
    user_id = current_user.id if current_user else None

    review = models.ProductReview(
        product_id=product.id,
        user_id=user_id,
        user_name=user_name,
        rating=review_in.rating,
        title=review_in.title,
        comment=review_in.comment
    )
    db.add(review)
    db.commit()

    # Recalculate average rating
    all_reviews = db.query(models.ProductReview).filter(models.ProductReview.product_id == product.id).all()
    avg_rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
    product.rating = avg_rating
    product.review_count = len(all_reviews)
    db.commit()
    db.refresh(review)

    return review

# -----------------------------------------------------------------------------
# Admin Protected Product Operations
# -----------------------------------------------------------------------------
@router.post("", response_model=schemas.ProductDetailResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Admin endpoint to create a new product with images and variants."""
    existing = db.query(models.Product).filter(models.Product.slug == product_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="A product with this slug already exists.")

    new_product = models.Product(
        name=product_in.name,
        slug=product_in.slug,
        description=product_in.description,
        material_details=product_in.material_details,
        price=product_in.price,
        discount_price=product_in.discount_price,
        category_id=product_in.category_id,
        gender=product_in.gender,
        is_featured=product_in.is_featured,
        is_trending=product_in.is_trending,
        is_new_arrival=product_in.is_new_arrival,
        is_active=True
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Add images
    for idx, img in enumerate(product_in.images):
        new_img = models.ProductImage(
            product_id=new_product.id,
            image_url=img.image_url,
            is_primary=img.is_primary or (idx == 0),
            display_order=img.display_order or idx
        )
        db.add(new_img)

    # Add variants
    for var in product_in.variants:
        sku = var.sku or f"{new_product.slug[:10].upper()}-{var.size}-{var.color[:3].upper()}"
        new_var = models.ProductVariant(
            product_id=new_product.id,
            size=var.size,
            color=var.color,
            sku=sku,
            stock_quantity=var.stock_quantity
        )
        db.add(new_var)

    db.commit()
    db.refresh(new_product)

    formatted = _format_product_list_item(new_product)
    formatted.update({
        "material_details": new_product.material_details,
        "images": new_product.images,
        "variants": new_product.variants,
        "reviews": new_product.reviews
    })
    return formatted

@router.put("/{product_id}", response_model=schemas.ProductListItemResponse)
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Admin endpoint to update product details."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    update_dict = product_in.model_dump(exclude_unset=True)
    for key, val in update_dict.items():
        setattr(product, key, val)

    db.commit()
    db.refresh(product)
    return _format_product_list_item(product)

@router.delete("/{product_id}", response_model=schemas.MessageResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Admin endpoint to soft-delete (deactivate) or remove product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    product.is_active = False
    db.commit()
    return {"message": f"Product '{product.name}' deactivated successfully.", "success": True}

@router.post("/{product_id}/stock", response_model=schemas.MessageResponse)
def update_variant_stock(
    product_id: int,
    stock_in: schemas.ProductStockUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Admin endpoint to update stock for a specific size/color variant."""
    variant = db.query(models.ProductVariant).filter(
        models.ProductVariant.id == stock_in.variant_id,
        models.ProductVariant.product_id == product_id
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found.")

    variant.stock_quantity = stock_in.stock_quantity
    db.commit()
    return {"message": f"Stock updated to {variant.stock_quantity} for {variant.size} / {variant.color}", "success": True}
