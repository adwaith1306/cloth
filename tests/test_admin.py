def test_admin_dashboard_stats(client, test_admin, sample_catalog):
    res = client.get("/api/admin/dashboard", headers=test_admin["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "total_sales" in data
    assert "total_orders" in data
    assert "total_products" in data
    assert data["total_products"] >= 1

def test_admin_order_status_update_and_restock(client, test_admin, sample_catalog, db_session):
    variant = sample_catalog["variants"][0]  # Size M, initial stock 10
    
    # 1. Place order
    res_order = client.post(
        "/api/orders",
        json={
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "+91 99999 88888",
            "shipping_address": "456 Avenue",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "items": [
                {
                    "product_id": sample_catalog["product"].id,
                    "size": "M",
                    "color": "Black",
                    "quantity": 2
                }
            ]
        }
    )
    order_id = res_order.json()["id"]

    db_session.refresh(variant)
    assert variant.stock_quantity == 8

    # 2. Admin updates status to Shipped
    res_status = client.patch(
        f"/api/admin/orders/{order_id}/status",
        json={"status": "Shipped"},
        headers=test_admin["headers"]
    )
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "Shipped"

    # 3. Admin cancels order -> Variant stock should be restored to 10
    res_cancel = client.patch(
        f"/api/admin/orders/{order_id}/status",
        json={"status": "Cancelled"},
        headers=test_admin["headers"]
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "Cancelled"

    db_session.refresh(variant)
    assert variant.stock_quantity == 10

def test_admin_coupon_management(client, test_admin):
    # Create coupon
    res_create = client.post(
        "/api/admin/coupons",
        json={
            "code": "SUPERVIP30",
            "discount_percent": 30.0,
            "min_purchase": 3000.0,
            "max_discount": 1500.0
        },
        headers=test_admin["headers"]
    )
    assert res_create.status_code == 201
    coupon_id = res_create.json()["id"]

    # List coupons
    res_list = client.get("/api/admin/coupons", headers=test_admin["headers"])
    assert res_list.status_code == 200
    codes = [c["code"] for c in res_list.json()]
    assert "SUPERVIP30" in codes

    # Delete coupon
    res_del = client.delete(f"/api/admin/coupons/{coupon_id}", headers=test_admin["headers"])
    assert res_del.status_code == 200
