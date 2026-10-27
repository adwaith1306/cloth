import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend import models
from backend.auth import get_password_hash, create_access_token

# Test SQLite in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database schema for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_admin(db_session):
    """Creates an admin user and returns user and token."""
    user = models.User(
        email="test_admin@vybe.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin Boss",
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": user.email, "role": user.role})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture(scope="function")
def test_customer(db_session):
    """Creates a regular customer and returns user and token."""
    user = models.User(
        email="test_cust@vybe.com",
        hashed_password=get_password_hash("CustPass123!"),
        full_name="Test Shopper",
        role="customer",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": user.email, "role": user.role})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture(scope="function")
def sample_catalog(db_session):
    """Creates a test category, product, variants, and coupon."""
    cat = models.Category(
        name="Hoodies",
        slug="hoodies",
        description="Premium hoodies"
    )
    db_session.add(cat)
    db_session.flush()

    prod = models.Product(
        name="Vybe Heavy Hoodie",
        slug="vybe-heavy-hoodie",
        description="Test hoodie description",
        material_details="100% Cotton",
        price=2999.0,
        discount_price=2499.0,
        category_id=cat.id,
        gender="Unisex",
        is_featured=True,
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    img = models.ProductImage(
        product_id=prod.id,
        image_url="https://example.com/hoodie.jpg",
        is_primary=True
    )
    db_session.add(img)

    v1 = models.ProductVariant(
        product_id=prod.id,
        size="M",
        color="Black",
        sku="VYBE-M-BLK",
        stock_quantity=10
    )
    v2 = models.ProductVariant(
        product_id=prod.id,
        size="L",
        color="Black",
        sku="VYBE-L-BLK",
        stock_quantity=5
    )
    db_session.add_all([v1, v2])

    coupon = models.Coupon(
        code="SAVE10",
        discount_percent=10.0,
        min_purchase=1000.0,
        is_active=True
    )
    db_session.add(coupon)
    db_session.commit()

    return {"category": cat, "product": prod, "variants": [v1, v2], "coupon": coupon}
