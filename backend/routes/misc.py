from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend import models, schemas

router = APIRouter(tags=["General & Catalog"])

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Returns all clothing categories with their active product counts."""
    categories = db.query(models.Category).order_by(models.Category.display_order.asc()).all()
    results = []
    for cat in categories:
        active_count = db.query(models.Product).filter(
            models.Product.category_id == cat.id,
            models.Product.is_active == True
        ).count()
        results.append({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "image_url": cat.image_url,
            "display_order": cat.display_order,
            "product_count": active_count
        })
    return results

@router.post("/newsletter", response_model=schemas.MessageResponse)
def subscribe_newsletter(sub: schemas.NewsletterSubscribe, db: Session = Depends(get_db)):
    """Registers an email address for fashion drops and VIP discount codes."""
    email = sub.email.lower().strip()
    existing = db.query(models.NewsletterSubscriber).filter(models.NewsletterSubscriber.email == email).first()
    if existing:
        return {"message": "You are already subscribed to the VYBE newsletter!", "success": True}

    new_sub = models.NewsletterSubscriber(email=email)
    db.add(new_sub)
    db.commit()
    return {"message": "Welcome to the VYBE Club! Check your inbox for exclusive perks.", "success": True}

@router.post("/contact", response_model=schemas.MessageResponse)
def submit_contact_form(msg: ContactMessage):
    """Processes customer inquiries from the contact page."""
    # In production, this can trigger an email notification or helpdesk ticket
    return {
        "message": f"Thank you, {msg.name}! Your message regarding '{msg.subject}' has been received. Our support team will get back to you within 24 hours.",
        "success": True
    }

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Application health and database connectivity probe."""
    try:
        # Check DB connection
        db.execute(models.User.__table__.select().limit(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "VYBE Clothing REST API",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status
    }
