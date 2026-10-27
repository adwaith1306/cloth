def test_get_products_list(client, sample_catalog):
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 1
    p = products[0]
    assert p["name"] == "Vybe Heavy Hoodie"
    assert "M" in p["available_sizes"]
    assert p["in_stock"] is True

def test_get_product_detail_by_slug(client, sample_catalog):
    res = client.get(f"/api/products/{sample_catalog['product'].slug}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Vybe Heavy Hoodie"
    assert len(data["variants"]) == 2
    assert len(data["images"]) == 1

def test_product_search_and_filter(client, sample_catalog):
    # Search
    res = client.get("/api/products?q=Heavy")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Search non-matching
    res = client.get("/api/products?q=NonExistentWord")
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Filter by category
    res = client.get(f"/api/products?category={sample_catalog['category'].slug}")
    assert res.status_code == 200
    assert len(res.json()) == 1

def test_add_product_review(client, sample_catalog, test_customer):
    res = client.post(
        f"/api/products/{sample_catalog['product'].id}/reviews",
        json={
            "rating": 5,
            "title": "Best purchase ever",
            "comment": "Incredible heavy cotton and boxy drop fit."
        },
        headers=test_customer["headers"]
    )
    assert res.status_code == 201
    review = res.json()
    assert review["rating"] == 5
    assert review["user_name"] == test_customer["user"].full_name

def test_admin_create_product(client, test_admin, sample_catalog):
    res = client.post(
        "/api/products",
        json={
            "name": "Admin Oversized Tee",
            "slug": "admin-oversized-tee",
            "description": "Premium oversized tee designed for streetwear lovers.",
            "material_details": "100% Cotton 280 GSM",
            "price": 1499.0,
            "discount_price": 1199.0,
            "category_id": sample_catalog["category"].id,
            "gender": "Unisex",
            "is_featured": True,
            "images": [
                {"image_url": "https://example.com/tee.jpg", "is_primary": True, "display_order": 0}
            ],
            "variants": [
                {"size": "L", "color": "Black", "stock_quantity": 20, "sku": "TEE-L-BLK"}
            ]
        },
        headers=test_admin["headers"]
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Admin Oversized Tee"

def test_customer_cannot_create_product(client, test_customer, sample_catalog):
    res = client.post(
        "/api/products",
        json={
            "name": "Hacked Product",
            "slug": "hacked-product",
            "description": "Unauthorized attempt",
            "price": 100.0,
            "category_id": sample_catalog["category"].id
        },
        headers=test_customer["headers"]
    )
    assert res.status_code == 403
