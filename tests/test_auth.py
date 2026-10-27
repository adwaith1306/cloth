def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecretPassword123!",
        "full_name": "Jordan Lee",
        "phone": "+91 98000 11122"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["role"] == "customer"

def test_register_duplicate_email(client, test_customer):
    res = client.post("/api/auth/register", json={
        "email": test_customer["user"].email,
        "password": "AnotherPassword123!",
        "full_name": "Copy Cat"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_login_success(client, test_customer):
    res = client.post("/api/auth/login", json={
        "email": "test_cust@vybe.com",
        "password": "CustPass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_cust@vybe.com"

def test_login_wrong_password(client, test_customer):
    res = client.post("/api/auth/login", json={
        "email": "test_cust@vybe.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

def test_get_me_authenticated(client, test_customer):
    res = client.get("/api/auth/me", headers=test_customer["headers"])
    assert res.status_code == 200
    assert res.json()["email"] == test_customer["user"].email

def test_get_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
