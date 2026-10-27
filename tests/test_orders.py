def test_validate_coupon_success(client, sample_catalog):
    res = client.post("/api/orders/validate-coupon", json={
        "code": "SAVE10",
        "subtotal": 2000.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 200.0  # 10% of 2000

def test_validate_coupon_min_purchase_failure(client, sample_catalog):
    res = client.post("/api/orders/validate-coupon", json={
        "code": "SAVE10",
        "subtotal": 500.0  # Below 1000 min
    })
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert "Minimum order value" in data["message"]

def test_create_order_end_to_end(client, sample_catalog, test_customer, db_session):
    variant = sample_catalog["variants"][0]  # Size M, stock 10
    initial_stock = variant.stock_quantity

    res = client.post(
        "/api/orders",
        json={
            "customer_name": "Test Shopper",
            "customer_email": "test_cust@vybe.com",
            "customer_phone": "+91 99999 88888",
            "shipping_address": "123 Street",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "country": "India",
            "payment_method": "COD",
            "coupon_code": "SAVE10",
            "items": [
                {
                    "product_id": sample_catalog["product"].id,
                    "size": "M",
                    "color": "Black",
                    "quantity": 2
                }
            ]
        },
        headers=test_customer["headers"]
    )

    assert res.status_code == 201
    order = res.json()
    assert order["order_number"].startswith("VYBE-")
    assert order["status"] == "Pending"
    assert len(order["items"]) == 1

    # Product discounted price is 2499.0
    # 2 items * 2499.0 = 4998.0 subtotal
    assert order["subtotal"] == 4998.0
    # 10% coupon = 499.8 discount
    assert order["discount_amount"] == 499.8
    # Free shipping since subtotal >= 1999
    assert order["shipping_fee"] == 0.0
    # Final total: 4998 - 499.8 = 4498.2
    assert order["total_amount"] == 4498.2

    # Verify inventory was decremented
    db_session.refresh(variant)
    assert variant.stock_quantity == initial_stock - 2

def test_create_order_insufficient_stock(client, sample_catalog):
    res = client.post(
        "/api/orders",
        json={
            "customer_name": "Greedy Buyer",
            "customer_email": "greedy@example.com",
            "customer_phone": "+91 99999 00000",
            "shipping_address": "123 Street",
            "city": "Delhi",
            "state": "Delhi",
            "postal_code": "110001",
            "items": [
                {
                    "product_id": sample_catalog["product"].id,
                    "size": "M",
                    "color": "Black",
                    "quantity": 999  # Far exceeds stock
                }
            ]
        }
    )
    assert res.status_code == 400
    assert "Insufficient stock" in res.json()["detail"]

def test_customer_my_orders(client, sample_catalog, test_customer):
    # Place an order first
    client.post(
        "/api/orders",
        json={
            "customer_name": "Test Shopper",
            "customer_email": test_customer["user"].email,
            "customer_phone": "+91 99999 88888",
            "shipping_address": "123 Street",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "items": [
                {
                    "product_id": sample_catalog["product"].id,
                    "size": "M",
                    "color": "Black",
                    "quantity": 1
                }
            ]
        },
        headers=test_customer["headers"]
    )

    res = client.get("/api/orders/my-orders", headers=test_customer["headers"])
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) >= 1
    assert orders[0]["customer_email"] == test_customer["user"].email
