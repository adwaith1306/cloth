/**
 * VYBE CLOTHING - CORE CLIENT SCRIPT (main.js)
 */

// Dynamically resolve API URL: Works when served by FastAPI or Live Server/External
const API_BASE = window.location.origin.includes(":8000") 
    ? "/api" 
    : "http://localhost:8000/api";

// -----------------------------------------------------------------------------
// Authentication State Management
// -----------------------------------------------------------------------------
function getAuthToken() {
    return localStorage.getItem("vybe_token");
}

function getCurrentUser() {
    const userStr = localStorage.getItem("vybe_user");
    if (!userStr) return null;
    try {
        return JSON.parse(userStr);
    } catch (e) {
        return null;
    }
}

function setAuth(token, user) {
    localStorage.setItem("vybe_token", token);
    localStorage.setItem("vybe_user", JSON.stringify(user));
    updateNavAuth();
}

function clearAuth() {
    localStorage.removeItem("vybe_token");
    localStorage.removeItem("vybe_user");
    updateNavAuth();
}

async function authFetch(endpoint, options = {}) {
    const token = getAuthToken();
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        // Token expired or invalid
        clearAuth();
        if (window.location.pathname.includes("account.html") || 
            window.location.pathname.includes("orders.html") || 
            window.location.pathname.includes("admin")) {
            window.location.href = "login.html";
        }
    }
    return response;
}

// -----------------------------------------------------------------------------
// Cart Storage Helpers
// -----------------------------------------------------------------------------
function getCart() {
    const cart = localStorage.getItem("vybe_cart");
    return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
    localStorage.setItem("vybe_cart", JSON.stringify(cart));
    updateCartCount();
}

function getCartCount() {
    const cart = getCart();
    return cart.reduce((sum, item) => sum + item.quantity, 0);
}

function updateCartCount() {
    const count = getCartCount();
    document.querySelectorAll(".cart-count-badge").forEach(badge => {
        badge.textContent = count;
        badge.style.display = count > 0 ? "flex" : "none";
    });
}

// -----------------------------------------------------------------------------
// Toast Notifications
// -----------------------------------------------------------------------------
function showToast(message, type = "success") {
    let container = document.getElementById("vybeToastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "vybeToastContainer";
        container.className = "toast-container-vybe";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast-vybe`;
    
    let icon = `<i class="bi bi-check-circle-fill text-success"></i>`;
    if (type === "danger" || type === "error") {
        icon = `<i class="bi bi-exclamation-octagon-fill text-danger"></i>`;
    } else if (type === "info") {
        icon = `<i class="bi bi-info-circle-fill text-info"></i>`;
    }

    toast.innerHTML = `
        <div style="font-size: 1.25rem;">${icon}</div>
        <div style="flex-grow: 1; font-size: 0.88rem; line-height: 1.35;">${message}</div>
        <button type="button" style="background:none; border:none; color:#888; cursor:pointer;" onclick="this.parentElement.remove()">
            <i class="bi bi-x-lg"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(20px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// -----------------------------------------------------------------------------
// Format Currency (Indian Rupee ₹)
// -----------------------------------------------------------------------------
function formatINR(amount) {
    if (amount === undefined || amount === null) return "₹0";
    return "₹" + Number(amount).toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });
}

// -----------------------------------------------------------------------------
// Dynamic Navbar Auth Dropdown
// -----------------------------------------------------------------------------
function updateNavAuth() {
    const userContainer = document.getElementById("navUserContainer");
    if (!userContainer) return;

    const user = getCurrentUser();

    if (user) {
        const isAdmin = user.role === "admin";
        userContainer.innerHTML = `
            <div class="dropdown">
                <button class="nav-icon-btn dropdown-toggle d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="bi bi-person-fill"></i>
                    <span class="d-none d-md-inline" style="font-size: 0.82rem; font-weight: 600;">${user.full_name.split(' ')[0]}</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow-lg" style="background: #171717; border: 1px solid rgba(255,255,255,0.15); border-radius: 0;">
                    <li><h6 class="dropdown-header text-uppercase" style="letter-spacing: 0.1em; color: #a3a3a3;">${user.email}</h6></li>
                    <li><a class="dropdown-item py-2" href="/account.html"><i class="bi bi-person me-2"></i> My Account</a></li>
                    <li><a class="dropdown-item py-2" href="/orders.html"><i class="bi bi-box-seam me-2"></i> My Orders</a></li>
                    ${isAdmin ? `
                        <li><hr class="dropdown-divider border-secondary"></li>
                        <li><a class="dropdown-item py-2 text-warning" href="/adminindex.html"><i class="bi bi-speedometer2 me-2"></i> Admin Portal</a></li>
                    ` : ''}
                    <li><hr class="dropdown-divider border-secondary"></li>
                    <li><a class="dropdown-item py-2 text-danger" href="javascript:void(0)" onclick="handleLogout()"><i class="bi bi-box-arrow-right me-2"></i> Logout</a></li>
                </ul>
            </div>
        `;
    } else {
        userContainer.innerHTML = `
            <a href="login.html" class="nav-icon-btn d-flex align-items-center gap-2 text-decoration-none">
                <i class="bi bi-person"></i>
                <span class="d-none d-md-inline tracking-wider-custom" style="font-size: 0.75rem; font-weight: 700;">LOGIN</span>
            </a>
        `;
    }
}

function handleLogout() {
    clearAuth();
    showToast("Logged out successfully.", "info");
    setTimeout(() => {
        window.location.href = "index.html";
    }, 500);
}

// -----------------------------------------------------------------------------
// Global Newsletter Handler
// -----------------------------------------------------------------------------
function setupNewsletter() {
    const form = document.getElementById("newsletterForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const emailInput = form.querySelector("input[type='email']");
        const email = emailInput.value.trim();
        if (!email) return;

        try {
            const res = await fetch(`${API_BASE}/newsletter`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            showToast(data.message || "Thank you for subscribing!", "success");
            emailInput.value = "";
        } catch (err) {
            showToast("Failed to subscribe. Please try again.", "danger");
        }
    });
}

// -----------------------------------------------------------------------------
// Initialize on DOM Ready
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    updateNavAuth();
    updateCartCount();
    setupNewsletter();
});
