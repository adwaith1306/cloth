from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal, Base, engine
from backend import models
from backend.auth import get_password_hash

def seed_database(db: Session):
    """
    Seeds initial categories, products, variants, images, coupons, and demo accounts.
    """
    # 1. Create Tables
    Base.metadata.create_all(bind=engine)

    # Check if already seeded
    if db.query(models.User).filter(models.User.email == "admin@vybe.com").first():
        print("Database already contains seed data.")
        return

    print("Seeding VYBE Clothing database...")

    # 2. Seed Users
    admin_user = models.User(
        email="admin@vybe.com",
        hashed_password=get_password_hash("VybeAdmin2026!"),
        full_name="Alexander Thorne",
        phone="+91 98765 43210",
        role="admin",
        is_active=True
    )
    db.add(admin_user)

    customer_user = models.User(
        email="alex@vybe.com",
        hashed_password=get_password_hash("Customer123!"),
        full_name="Alex Rivera",
        phone="+91 98123 45678",
        role="customer",
        is_active=True
    )
    db.add(customer_user)
    db.commit()

    # Seed Address for customer
    cust_address = models.ShippingAddress(
        user_id=customer_user.id,
        full_name="Alex Rivera",
        phone="+91 98123 45678",
        street_address="Flat 402, Highline Residency, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400050",
        country="India",
        is_default=True
    )
    db.add(cust_address)

    # 3. Seed Categories
    categories_data = [
        {
            "name": "Hoodies & Sweatshirts",
            "slug": "hoodies-sweatshirts",
            "description": "Heavyweight 400 GSM French Terry hoodies and relaxed streetwear crewnecks.",
            "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=800&q=80",
            "display_order": 1
        },
        {
            "name": "T-Shirts & Tops",
            "slug": "t-shirts",
            "description": "Boxy-fit oversized graphic tees and luxurious drop-shoulder staples.",
            "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80",
            "display_order": 2
        },
        {
            "name": "Jackets & Outerwear",
            "slug": "jackets",
            "description": "Utility bomber jackets, cropped windbreakers, and modular outerwear.",
            "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=800&q=80",
            "display_order": 3
        },
        {
            "name": "Jeans & Trousers",
            "slug": "jeans-trousers",
            "description": "Relaxed-fit cargo pants, Japanese washed denim, and tailored parachute bottoms.",
            "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=800&q=80",
            "display_order": 4
        },
        {
            "name": "Shirts",
            "slug": "shirts",
            "description": "Cuban collar resort shirts, brushed flannel overshirts, and textured poplin.",
            "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80",
            "display_order": 5
        },
        {
            "name": "Accessories",
            "slug": "accessories",
            "description": "Minimalist crossbody tactical bags, washed caps, and stainless streetwear chains.",
            "image_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=800&q=80",
            "display_order": 6
        }
    ]

    cat_map = {}
    for c in categories_data:
        cat_obj = models.Category(**c)
        db.add(cat_obj)
        db.flush()
        cat_map[cat_obj.slug] = cat_obj.id

    # 4. Seed Products
    products_data = [
        {
            "name": "Oversized 'NO SIGNAL' Heavyweight Hoodie",
            "slug": "oversized-no-signal-hoodie",
            "category_slug": "hoodies-sweatshirts",
            "gender": "Unisex",
            "price": 3499.0,
            "discount_price": 2799.0,
            "description": "Engineered with ultra-soft 450 GSM French Terry cotton. Features a double-layered hood without drawstrings for a clean contemporary drape, deep kangaroo pocket, and high-density puffed screenprint across the back.",
            "material_details": "100% Combed Heavy Cotton (450 GSM). Pre-shrunk, fleece interior, ribbed cuffs and hem.",
            "rating": 4.9,
            "review_count": 38,
            "is_featured": True,
            "is_trending": True,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=1000&q=80", False),
                ("https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Washed Charcoal", 12),
                ("M", "Washed Charcoal", 25),
                ("L", "Washed Charcoal", 18),
                ("XL", "Washed Charcoal", 8),
                ("M", "Oatmeal Beige", 15),
                ("L", "Oatmeal Beige", 10),
            ]
        },
        {
            "name": "Raw Hem Boxy Drop-Shoulder Tee",
            "slug": "raw-hem-boxy-drop-shoulder-tee",
            "category_slug": "t-shirts",
            "gender": "Men",
            "price": 1899.0,
            "discount_price": 1499.0,
            "description": "A silhouette crafted for modern street culture. Custom boxy cut with lowered shoulder seams, wide collar binding, and a distressed raw hemline for effortless layering.",
            "material_details": "100% Organic Pima Cotton (260 GSM). Silicon washed for ultimate hand feel.",
            "rating": 4.8,
            "review_count": 52,
            "is_featured": True,
            "is_trending": True,
            "is_new_arrival": False,
            "images": [
                ("https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Matte Black", 20),
                ("M", "Matte Black", 35),
                ("L", "Matte Black", 28),
                ("XL", "Matte Black", 14),
                ("M", "Vintage Cream", 22),
                ("L", "Vintage Cream", 19)
            ]
        },
        {
            "name": "Cyber-Utility Flight Bomber Jacket",
            "slug": "cyber-utility-flight-bomber",
            "category_slug": "jackets",
            "gender": "Unisex",
            "price": 5999.0,
            "discount_price": 4999.0,
            "description": "Tactical streetwear outerwear at its peak. Weather-resistant matte nylon shell with signature sleeve utility pocket, heavy two-way YKK front zipper, and internal carry straps.",
            "material_details": "Nylon Ripstop Shell with Water-Repellent DWR Finish. Quilted satin lining with 80g thermal insulation.",
            "rating": 5.0,
            "review_count": 27,
            "is_featured": True,
            "is_trending": True,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Stealth Black", 8),
                ("M", "Stealth Black", 14),
                ("L", "Stealth Black", 12),
                ("XL", "Stealth Black", 6),
                ("L", "Olive Sage", 7)
            ]
        },
        {
            "name": "Wide-Leg Multi-Pocket Cargo Trousers",
            "slug": "wide-leg-multi-pocket-cargo",
            "category_slug": "jeans-trousers",
            "gender": "Unisex",
            "price": 3299.0,
            "discount_price": 2699.0,
            "description": "Architectural volume tailored with relaxed ergonomics. Equipped with 8 functional 3D cargo pockets, adjustable bungee drawstrings at the ankle hems, and reinforced knee dart articulation.",
            "material_details": "100% Heavy Cotton Twill (320 GSM). Enzyme stone-washed for soft structure.",
            "rating": 4.7,
            "review_count": 41,
            "is_featured": True,
            "is_trending": False,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Washed Black", 10),
                ("M", "Washed Black", 18),
                ("L", "Washed Black", 15),
                ("XL", "Washed Black", 9),
                ("M", "Desert Sand", 12),
                ("L", "Desert Sand", 11)
            ]
        },
        {
            "name": "Minimalist Corduroy Overshirt",
            "slug": "minimalist-corduroy-overshirt",
            "category_slug": "shirts",
            "gender": "Men",
            "price": 2799.0,
            "discount_price": 2299.0,
            "description": "Rich 8-wale plush cotton corduroy with a structured overshirt silhouette. Wear it buttoned as a statement jacket or open over a white tank for that clean Tokyo minimalist aesthetic.",
            "material_details": "100% High-Grade Cotton Corduroy. Horn-effect custom engraved VYBE buttons.",
            "rating": 4.9,
            "review_count": 19,
            "is_featured": False,
            "is_trending": True,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Espresso Brown", 10),
                ("M", "Espresso Brown", 16),
                ("L", "Espresso Brown", 14),
                ("XL", "Espresso Brown", 7),
                ("M", "Slate Olive", 8)
            ]
        },
        {
            "name": "Cropped Acid-Wash Baby Tee",
            "slug": "cropped-acid-wash-baby-tee",
            "category_slug": "t-shirts",
            "gender": "Women",
            "price": 1499.0,
            "discount_price": 1199.0,
            "description": "Y2K street-luxe revival piece. Fitted cropped cut with custom acid-wash texture, contrast coverstitch detailing, and subtle tonal embroidery.",
            "material_details": "95% Ribbed Organic Cotton, 5% Elastane for structured contour fit.",
            "rating": 4.8,
            "review_count": 29,
            "is_featured": True,
            "is_trending": True,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("XS", "Washed Ash", 15),
                ("S", "Washed Ash", 20),
                ("M", "Washed Ash", 18),
                ("L", "Washed Ash", 9),
                ("S", "Vintage White", 12),
                ("M", "Vintage White", 10)
            ]
        },
        {
            "name": "Parachute Utility Track Pant",
            "slug": "parachute-utility-track-pant",
            "category_slug": "jeans-trousers",
            "gender": "Women",
            "price": 2999.0,
            "discount_price": 2499.0,
            "description": "Effortless balloon silhouette cut from ultralight matte tech-poplin. Featuring elasticated high waist with cord lock, articulated knee pleats, and deep side slash pockets.",
            "material_details": "100% Crisp Tech Nylon Poplin. Breathable, anti-static, quick dry.",
            "rating": 4.9,
            "review_count": 33,
            "is_featured": False,
            "is_trending": True,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1509551388413-e18d0ac5d495?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("XS", "Bone White", 8),
                ("S", "Bone White", 14),
                ("M", "Bone White", 12),
                ("L", "Bone White", 6),
                ("S", "Shadow Grey", 10),
                ("M", "Shadow Grey", 15)
            ]
        },
        {
            "name": "Heavyweight French Terry Zip Hoodie",
            "slug": "heavyweight-french-terry-zip-hoodie",
            "category_slug": "hoodies-sweatshirts",
            "gender": "Unisex",
            "price": 3799.0,
            "discount_price": 3199.0,
            "description": "The quintessential modern layer. Built with custom two-way polished silver hardware, an exaggerated double-lined hood, and seamless drop-shoulder architecture.",
            "material_details": "420 GSM 100% Loopback French Terry Cotton. Anti-pilling silicone bath finish.",
            "rating": 5.0,
            "review_count": 22,
            "is_featured": True,
            "is_trending": False,
            "is_new_arrival": False,
            "images": [
                ("https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Anthracite", 11),
                ("M", "Anthracite", 19),
                ("L", "Anthracite", 17),
                ("XL", "Anthracite", 8),
                ("M", "Fog Grey", 14)
            ]
        },
        {
            "name": "Modular Tactical Crossbody Sling Bag",
            "slug": "modular-tactical-crossbody-bag",
            "category_slug": "accessories",
            "gender": "Unisex",
            "price": 1999.0,
            "discount_price": 1499.0,
            "description": "Everyday carry reimagined. Water-resistant ballistic Cordura exterior with quick-release magnetic Fidlock buckle, waterproof tape zippers, and compartmentalized tech organizers.",
            "material_details": "1000D Cordura Nylon, YKK Aquaguard Zippers, Nylon Webbing Strap.",
            "rating": 4.9,
            "review_count": 48,
            "is_featured": False,
            "is_trending": True,
            "is_new_arrival": False,
            "images": [
                ("https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("Free Size", "Matte Black", 30),
                ("Free Size", "Coyote Tan", 20)
            ]
        },
        {
            "name": "Heavy Distressed Denim Trucker Jacket",
            "slug": "heavy-distressed-denim-trucker",
            "category_slug": "jackets",
            "gender": "Men",
            "price": 4999.0,
            "discount_price": 4199.0,
            "description": "14oz rigid Japanese selvedge-inspired denim with authentic vintage distressing, hand-abraded collars, and custom matte silver branded hardware.",
            "material_details": "100% Heavy Selvedge-look Cotton Denim (14 oz). Custom oxidized brass buttons.",
            "rating": 4.8,
            "review_count": 16,
            "is_featured": False,
            "is_trending": False,
            "is_new_arrival": True,
            "images": [
                ("https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Vintage Bleach Wash", 6),
                ("M", "Vintage Bleach Wash", 12),
                ("L", "Vintage Bleach Wash", 9),
                ("XL", "Vintage Bleach Wash", 4)
            ]
        },
        {
            "name": "Oversized Flannel Plaid Workshirt",
            "slug": "oversized-flannel-plaid-workshirt",
            "category_slug": "shirts",
            "gender": "Unisex",
            "price": 2499.0,
            "discount_price": 1999.0,
            "description": "Double-brushed heavyweight cotton flannel in custom neutral earth-tone tartan. Featuring drop shoulders, twin chest patch pockets, and a scooped hemline.",
            "material_details": "100% Double-Brushed Yarn-Dyed Cotton Flannel (280 GSM).",
            "rating": 4.7,
            "review_count": 25,
            "is_featured": False,
            "is_trending": False,
            "is_new_arrival": False,
            "images": [
                ("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=1000&q=80", True),
                ("https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=1000&q=80", False)
            ],
            "variants": [
                ("S", "Oatmeal Plaid", 10),
                ("M", "Oatmeal Plaid", 15),
                ("L", "Oatmeal Plaid", 12),
                ("XL", "Oatmeal Plaid", 5)
            ]
        },
        {
            "name": "Signature Embroidered Washed Dad Cap",
            "slug": "signature-embroidered-dad-cap",
            "category_slug": "accessories",
            "gender": "Unisex",
            "price": 1299.0,
            "discount_price": 999.0,
            "description": "Unstructured 6-panel low profile cap crafted from pigment-washed chino cotton. Finished with clean 3D tonal VYBE typography embroidery and an antiqued brass buckle strap.",
            "material_details": "100% Pigment-Dyed Cotton Twill. Breathable sewn eyelets.",
            "rating": 4.9,
            "review_count": 31,
            "is_featured": False,
            "is_trending": False,
            "is_new_arrival": False,
            "images": [
                ("https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=1000&q=80", True)
            ],
            "variants": [
                ("Free Size", "Washed Black", 25),
                ("Free Size", "Khaki Stone", 20)
            ]
        }
    ]

    for p in products_data:
        cat_id = cat_map[p["category_slug"]]
        product = models.Product(
            name=p["name"],
            slug=p["slug"],
            description=p["description"],
            material_details=p["material_details"],
            price=p["price"],
            discount_price=p["discount_price"],
            category_id=cat_id,
            gender=p["gender"],
            rating=p["rating"],
            review_count=p["review_count"],
            is_featured=p["is_featured"],
            is_trending=p["is_trending"],
            is_new_arrival=p["is_new_arrival"],
            is_active=True
        )
        db.add(product)
        db.flush()

        # Add images
        for idx, (img_url, is_prim) in enumerate(p["images"]):
            img = models.ProductImage(
                product_id=product.id,
                image_url=img_url,
                is_primary=is_prim,
                display_order=idx
            )
            db.add(img)

        # Add variants
        for size, color, stock in p["variants"]:
            sku = f"VYBE-{p['slug'][:6].upper()}-{size}-{color[:3].upper()}"
            variant = models.ProductVariant(
                product_id=product.id,
                size=size,
                color=color,
                sku=sku,
                stock_quantity=stock
            )
            db.add(variant)

        # Add 1-2 realistic customer reviews per product
        rev = models.ProductReview(
            product_id=product.id,
            user_name="Aryan K.",
            rating=5,
            title="Insane quality and heavyweight drape",
            comment="Honestly blown away by the fabric thickness. Rivals luxury streetwear brands that charge 5x more. Sizing is intentionally boxy and looks phenomenal."
        )
        db.add(rev)

    # 5. Seed Coupons
    coupons = [
        models.Coupon(
            code="WELCOME10",
            discount_percent=10.0,
            min_purchase=999.0,
            max_discount=500.0,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=365)
        ),
        models.Coupon(
            code="STREETVYBE20",
            discount_percent=20.0,
            min_purchase=2499.0,
            max_discount=1000.0,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=180)
        ),
        models.Coupon(
            code="FLAT500",
            discount_amount=500.0,
            min_purchase=3000.0,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
    ]
    for c in coupons:
        db.add(c)

    # 6. Seed a sample past order for customer Alex
    sample_order = models.Order(
        order_number="VYBE-20261027-C9D1",
        user_id=customer_user.id,
        customer_name="Alex Rivera",
        customer_email="alex@vybe.com",
        customer_phone="+91 98123 45678",
        shipping_address="Flat 402, Highline Residency, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400050",
        country="India",
        payment_method="COD",
        payment_status="Confirmed",
        subtotal=2799.0,
        discount_amount=279.9,
        shipping_fee=0.0,
        total_amount=2519.1,
        status="Shipped",
        notes="Please leave at reception if not available.",
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db.add(sample_order)
    db.flush()

    first_prod = db.query(models.Product).first()
    if first_prod:
        sample_item = models.OrderItem(
            order_id=sample_order.id,
            product_id=first_prod.id,
            product_name=first_prod.name,
            size="L",
            color="Washed Charcoal",
            unit_price=2799.0,
            quantity=1,
            subtotal=2799.0,
            image_url=first_prod.primary_image
        )
        db.add(sample_item)

    db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
