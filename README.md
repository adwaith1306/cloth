# VYBE Clothing — Full-Stack E-Commerce Platform

A contemporary streetwear and luxury fashion e-commerce application engineered with **Python (FastAPI)**, **SQLAlchemy ORM**, **SQLite**, **HTML5/CSS3/JavaScript (ES6+)**, and **Bootstrap 5**.

![Brand Aesthetic](https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1200&q=80)

---

## Table of Contents
1. [Key Features](#key-features)
2. [Project Architecture](#project-architecture)
3. [Prerequisites](#prerequisites)
4. [Local Setup & Running](#local-setup--running)
5. [Demo Credentials & Seed Data](#demo-credentials--seed-data)
6. [API Endpoints & Swagger Documentation](#api-endpoints--swagger-documentation)
7. [Running Automated Tests](#running-automated-tests)
8. [AWS EC2 & Nginx Deployment Guide](#aws-ec2--nginx-deployment-guide)
9. [Git & GitHub Version Control](#git--github-version-control)

---

## 1. Key Features

### Frontend (Streetwear Aesthetic & Client Experience)
- **Minimalist Luxury Streetwear Design:** Deep black, carbon gray, and warm beige stone tones with bold typography (`Outfit` & `Space Grotesk`).
- **Interactive Catalog & Filters:** Real-time search, category filtering (Hoodies, Tees, Jackets, Cargos, Shirts, Accessories), gender segmentation (Men, Women, Unisex), size filtering (XS to XXL), and price slider.
- **Dynamic Product Detail Page:**
  - Multi-angle image gallery with interactive thumbnail switcher.
  - Variant selection (Size and Color) with live stock notifications (*"Only 2 units remaining"*).
  - Size Guide Modal with chest, length, and shoulder measurements.
  - Customer review submission with live rating recalculation.
  - Related product recommendations.
- **Persistent Shopping Bag:** Stored in `localStorage`, quantity controls bounded by actual available inventory, free-shipping threshold tracker (₹1,999), and promo coupon validation.
- **Checkout Flow:** Guest and authenticated customer checkout, saved delivery addresses, and **Cash on Delivery (COD)** payment with architecture ready for Razorpay/UPI gateway integration.
- **Customer Portal:** Profile manager, shipping addresses CRUD, order history, and tracking statuses.
- **Protected Admin Dashboard:** Real-time KPI metrics (gross revenue, order counts, pending dispatches, low-stock warnings), order fulfillment status updater (with inventory restocking on cancellation), product catalog creation with size variants, and promotional coupon management.

### Backend (FastAPI Architecture & Business Logic)
- **Strict Server-Side Validation:** Prices and subtotals are always determined from the database, preventing client-side price tampering.
- **Atomic Inventory Control:** Inventory is safely decremented inside a database transaction during checkout; cancelling an order automatically returns the stock to the catalog.
- **JWT Authentication & RBAC:** Secure password hashing (bcrypt) and role-based access control distinguishing `customer` and `admin`.
- **Database ORM:** SQLAlchemy with SQLite (cleanly portable to PostgreSQL/MySQL via `.env`).
- **Single-Port Local Serving:** FastAPI serves the backend REST APIs at `/api`, Swagger docs at `/docs`, and mounts the frontend static directory directly at `http://localhost:8000/`.

---

## 2. Project Architecture

```text
vybe-clothing/
├── backend/
│   ├── main.py              # FastAPI app, CORS, routes & static files mount
│   ├── config.py            # Environment settings (Pydantic BaseSettings)
│   ├── database.py          # SQLAlchemy engine, session maker & get_db dependency
│   ├── models.py            # Relational database models (User, Product, Order, etc.)
│   ├── schemas.py           # Pydantic v2 validation schemas
│   ├── auth.py              # Password hashing (bcrypt) & JWT token handlers
│   ├── seed.py              # Realistic sample catalog, coupons & demo accounts
│   ├── routes/
│   │   ├── auth.py          # Register, login, profile & address endpoints
│   │   ├── products.py      # Catalog filtering, search, slug lookup & reviews
│   │   ├── orders.py        # Order placement, coupons & tracking
│   │   ├── admin.py         # KPIs, order fulfillment & coupon management
│   │   └── misc.py          # Categories, newsletter & health probe
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Homepage (Hero, drops, lookbook, reviews)
│   ├── shop.html            # Catalog with dynamic filters and sorting
│   ├── product.html         # Product gallery, variant picker & reviews
│   ├── cart.html            # Shopping bag with coupon discount calculation
│   ├── checkout.html        # Shipping address & Cash on Delivery (COD)
│   ├── login.html           # Login with 1-click demo credential autofill
│   ├── register.html        # Customer registration
│   ├── account.html         # Profile & saved shipping addresses
│   ├── orders.html          # Order history & fulfillment tracking
│   ├── about.html           # Brand story & heavyweight cotton craftsmanship
│   ├── contact.html         # Customer concierge & interactive FAQs
│   ├── admin/
│   │   └── index.html       # Protected Admin Portal
│   ├── css/
│   │   └── style.css        # Luxury streetwear design system
│   └── js/
│       ├── main.js          # Auth state, cart counter, toast notifications
│       ├── products.js      # Catalog filtering, gallery & review engine
│       ├── cart.js          # Cart state, shipping bar & coupon discount logic
│       ├── checkout.js      # Address selection & order placement
│       └── admin.js         # Admin KPIs, orders & catalog management
├── tests/
│   ├── conftest.py          # In-memory test database & FastAPI TestClient fixtures
│   ├── test_auth.py         # Authentication and registration tests
│   ├── test_products.py     # Catalog, search, filtering & reviews tests
│   ├── test_orders.py       # Price calculation, coupon & inventory tests
│   └── test_admin.py        # Admin stats, order status & restock tests
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
└── README.md                # Comprehensive documentation
```

---

## 3. Prerequisites

- **Python 3.10+** (Python 3.10, 3.11, or 3.12 recommended)
- **pip** (Python package installer)
- Modern web browser (Chrome, Edge, Firefox, Safari)

---

## 4. Local Setup & Running

### Step 1: Clone or Navigate to the Project Directory
```bash
cd C:\Users\user\.gemini\antigravity\scratch\vybe-clothing
```

### Step 2: Create and Activate a Python Virtual Environment
```bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example environment template to `.env`:
```bash
cp .env.example .env
```
The default values in `.env.example` work out of the box with SQLite.

### Step 5: Start the FastAPI Server
The application automatically seeds the database with sample products, categories, coupons, and demo accounts on first launch!
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Open the Website
- **Storefront:** Visit `http://localhost:8000/` or `http://localhost:8000/index.html` in your browser.
- **Admin Portal:** Visit `http://localhost:8000/admin/index.html`.
- **Interactive Swagger API Docs:** Visit `http://localhost:8000/docs`.

*(Optional)* If you prefer using VS Code Live Server or external static hosting (e.g. `http://127.0.0.1:5500/frontend/index.html`), the frontend automatically detects the port difference and routes all REST API requests to `http://localhost:8000/api` through configured CORS.

---

## 5. Demo Credentials & Seed Data

The database comes pre-loaded with sample accounts (you can also use the **1-Click Demo Buttons** on `login.html`):

| Role | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@vybe.com` | `VybeAdmin2026!` | Access `/admin/index.html`, manage orders, create products, restock variants, manage coupons |
| **Customer** | `alex@vybe.com` | `Customer123!` | Standard customer account with sample past order and saved Mumbai shipping address |

### Active Promotional Coupons:
- **`WELCOME10`**: 10% discount on orders above ₹999 (capped at ₹500).
- **`STREETVYBE20`**: 20% discount on orders above ₹2,499 (capped at ₹1,000).
- **`FLAT500`**: Flat ₹500 off on orders above ₹3,000.

---

## 6. API Endpoints & Swagger Documentation

Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Register a customer account and receive a JWT.
- `POST /api/auth/login` — Authenticate using email and password.
- `GET /api/auth/me` — Retrieve current authenticated user profile.
- `PUT /api/auth/profile` — Update name or phone number.
- `PUT /api/auth/change-password` — Securely update password.
- `GET /api/auth/addresses` — Retrieve saved shipping addresses.
- `POST /api/auth/addresses` — Save a new shipping address.
- `DELETE /api/auth/addresses/{id}` — Delete a saved address.

### Products Catalog (`/api/products`)
- `GET /api/products` — Filter products by category, gender, size, color, price range, and sort order.
- `GET /api/products/featured` — Retrieve top featured products.
- `GET /api/products/trending` — Retrieve trending streetwear pieces.
- `GET /api/products/new-arrivals` — Retrieve new drop releases.
- `GET /api/products/{id_or_slug}` — Retrieve full product details, all images, variants, stock, and reviews.
- `POST /api/products/{id}/reviews` — Submit a rating and review for a product.
- `POST /api/products` *(Admin only)* — Create a new product with images and size variants.
- `PUT /api/products/{id}` *(Admin only)* — Update product details.
- `DELETE /api/products/{id}` *(Admin only)* — Deactivate a product.
- `POST /api/products/{id}/stock` *(Admin only)* — Update variant inventory stock count.

### Orders & Checkout (`/api/orders`)
- `POST /api/orders/validate-coupon` — Validate a promo code against a cart subtotal.
- `POST /api/orders` — Accept an order, calculate totals on the server, validate and deduct inventory.
- `GET /api/orders/my-orders` — Retrieve logged-in customer's order history.
- `GET /api/orders/{id_or_number}` — Retrieve order details (authorized owner or admin).

### Admin Portal (`/api/admin`)
- `GET /api/admin/dashboard` — KPI metrics (sales, order counts, pending dispatches, low stock count).
- `GET /api/admin/orders` — List and filter customer orders with search.
- `PATCH /api/admin/orders/{id}/status` — Update order status (Pending, Confirmed, Processing, Shipped, Delivered, Cancelled); automatically restocks items on cancellation.
- `GET /api/admin/low-stock` — List variants with inventory ≤ 5 units.
- `GET /api/admin/coupons` — List all promo coupons.
- `POST /api/admin/coupons` — Create a new promo coupon.
- `DELETE /api/admin/coupons/{id}` — Delete a promo coupon.

### General & Health
- `GET /api/categories` — List clothing categories with active product counts.
- `POST /api/newsletter` — Register email for newsletter drops.
- `POST /api/contact` — Submit customer concierge inquiries.
- `GET /api/health` — Service and database health probe.

---

## 7. Running Automated Tests

The test suite in `tests/` covers unit and integration tests using `pytest` and `httpx`.

To run all tests:
```bash
pytest
```

To run with verbose output:
```bash
pytest -v
```

### What the test suite verifies:
1. **User Authentication:** Registration, duplicate email rejection, login verification, wrong password handling, JWT decoding.
2. **Product Catalog:** Querying products, category filtering, search queries, sort orders, slug lookup, customer reviews, admin authorization enforcement.
3. **Cart & Orders:** Server-side pricing calculation, coupon validation and discount limits, inventory stock deduction, out-of-stock rejection, customer order history isolation.
4. **Admin Dashboard:** Business KPIs, order fulfillment status updates, automatic inventory restocking upon cancellation, coupon creation and deletion.

---

## 8. AWS EC2 & Nginx Deployment Guide

Deploying VYBE Clothing on an **Ubuntu 22.04 / 24.04 LTS** instance on AWS EC2.

### Step 1: Provision EC2 Instance
- Launch an EC2 instance (e.g. `t3.small` or `t3.micro`).
- In the Security Group, open inbound ports:
  - `SSH (22)`
  - `HTTP (80)`
  - `HTTPS (443)`

### Step 2: Connect and Install System Dependencies
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git certbot python3-certbot-nginx -y
```

### Step 3: Clone Repository and Setup Virtualenv
```bash
cd /var/www
sudo git clone https://github.com/your-username/vybe-clothing.git
sudo chown -R ubuntu:ubuntu /var/www/vybe-clothing
cd /var/www/vybe-clothing

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Step 4: Configure Production Environment
```bash
cp .env.example .env
nano .env
# Set a strong SECRET_KEY and configure DATABASE_URL (SQLite or PostgreSQL)
```

### Step 5: Create Systemd Service for Gunicorn / Uvicorn
Create a systemd unit file at `/etc/systemd/system/vybe.service`:
```ini
[Unit]
Description=VYBE Clothing FastAPI Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/vybe-clothing
Environment="PATH=/var/www/vybe-clothing/venv/bin"
ExecStart=/var/www/vybe-clothing/venv/bin/uvicorn backend.main:app --workers 3 --host 127.0.0.1 --port 8000

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start vybe
sudo systemctl enable vybe
sudo systemctl status vybe
```

### Step 6: Configure Nginx as a Reverse Proxy
Create `/etc/nginx/sites-available/vybe`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Static assets caching
    location /frontend/ {
        alias /var/www/vybe-clothing/frontend/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # Pass all requests to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/vybe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Enable SSL Certificate via Let's Encrypt
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 9. Git & GitHub Version Control

To initialize and push this project to your GitHub repository:

```bash
# 1. Initialize Git repository
git init

# 2. Stage all files
git add .

# 3. Create initial commit
git commit -m "feat: complete full-stack VYBE clothing e-commerce platform"

# 4. Link to GitHub repository
git branch -M main
git remote add origin https://github.com/your-username/vybe-clothing.git

# 5. Push code
git push -u origin main
```

---

## License
MIT License. Crafted with contemporary streetwear passion by the VYBE Engineering Team.
