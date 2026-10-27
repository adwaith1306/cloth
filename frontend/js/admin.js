/**
 * VYBE CLOTHING - ADMIN DASHBOARD CONTROLLER (admin.js)
 */

let allAdminOrders = [];
let allAdminProducts = [];

async function checkAdminAuth() {
    const user = getCurrentUser();
    if (!user || user.role !== "admin") {
        showToast("Administrative access required.", "danger");
        setTimeout(() => {
            window.location.href = "/login.html";
        }, 800);
        return false;
    }
    const adminNameEl = document.getElementById("adminUserBadge");
    if (adminNameEl) adminNameEl.textContent = user.full_name;
    return true;
}

async function initAdminDashboard() {
    const isAuthed = await checkAdminAuth();
    if (!isAuthed) return;

    loadDashboardStats();
    loadAdminOrders();
    loadAdminProducts();
    loadAdminCoupons();
    loadCategoriesDropdown();
    setupAdminTabs();
}

// -----------------------------------------------------------------------------
// KPI Stats
// -----------------------------------------------------------------------------
async function loadDashboardStats() {
    try {
        const res = await authFetch("/admin/dashboard");
        if (!res.ok) throw new Error();
        const data = await res.json();

        document.getElementById("kpiTotalSales").textContent = formatINR(data.total_sales);
        document.getElementById("kpiTotalOrders").textContent = data.total_orders;
        document.getElementById("kpiTotalProducts").textContent = data.total_products;
        document.getElementById("kpiTotalCustomers").textContent = data.total_customers;
        document.getElementById("kpiPendingOrders").textContent = data.pending_orders;
        document.getElementById("kpiLowStock").textContent = data.low_stock_count;

        // Load low stock alerts
        loadLowStockList();
    } catch (e) {
        showToast("Failed to load dashboard metrics.", "danger");
    }
}

async function loadLowStockList() {
    const container = document.getElementById("lowStockTableBody");
    if (!container) return;

    try {
        const res = await authFetch("/admin/low-stock?threshold=5");
        const items = await res.json();

        if (items.length === 0) {
            container.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">All variants well stocked!</td></tr>`;
            return;
        }

        container.innerHTML = items.map(item => `
            <tr>
                <td>
                    <img src="${item.primary_image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=80&q=80'}" style="width: 38px; height: 48px; object-fit: cover;">
                </td>
                <td class="fw-bold">${item.product_name}</td>
                <td><span class="badge bg-secondary font-mono">${item.size}</span> / ${item.color}</td>
                <td><span class="badge bg-danger">${item.stock_quantity} left</span></td>
                <td>
                    <button class="btn btn-sm btn-vybe-outline py-1 px-2" onclick="promptRestock(${item.product_id}, ${item.variant_id}, '${item.size}', '${item.color}')">
                        Restock
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Low stock query failed", e);
    }
}

async function promptRestock(productId, variantId, size, color) {
    const newQtyStr = prompt(`Enter new total stock count for ${size} / ${color}:`, "20");
    if (newQtyStr === null) return;
    const qty = parseInt(newQtyStr);
    if (isNaN(qty) || qty < 0) {
        showToast("Invalid stock quantity.", "danger");
        return;
    }

    try {
        const res = await authFetch(`/products/${productId}/stock`, {
            method: "POST",
            body: JSON.stringify({ variant_id: variantId, stock_quantity: qty })
        });
        if (res.ok) {
            showToast(`Updated stock to ${qty}`, "success");
            loadDashboardStats();
            loadAdminProducts();
        } else {
            showToast("Failed to update stock.", "danger");
        }
    } catch (e) {
        showToast("Error updating stock.", "danger");
    }
}

// -----------------------------------------------------------------------------
// Orders Management
// -----------------------------------------------------------------------------
async function loadAdminOrders() {
    const container = document.getElementById("adminOrdersList");
    if (!container) return;

    container.innerHTML = `<div class="text-center py-5"><div class="spinner-border text-light"></div></div>`;

    try {
        const res = await authFetch("/admin/orders");
        allAdminOrders = await res.json();
        renderFilteredOrders();
    } catch (e) {
        container.innerHTML = `<div class="text-danger py-4">Failed to load orders.</div>`;
    }
}

function renderFilteredOrders() {
    const container = document.getElementById("adminOrdersList");
    const statusFilter = document.getElementById("orderStatusFilter").value;
    const searchQuery = document.getElementById("orderSearchInput").value.trim().toLowerCase();

    let filtered = allAdminOrders.filter(order => {
        const matchesStatus = !statusFilter || order.status.toLowerCase() === statusFilter.toLowerCase();
        const matchesSearch = !searchQuery || 
            order.order_number.toLowerCase().includes(searchQuery) ||
            order.customer_name.toLowerCase().includes(searchQuery) ||
            order.customer_email.toLowerCase().includes(searchQuery) ||
            order.customer_phone.includes(searchQuery);
        return matchesStatus && matchesSearch;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                No orders match your criteria.
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(o => {
        const statusClass = `status-${o.status.toLowerCase()}`;
        return `
            <div class="p-4 mb-3" style="background: var(--bg-surface); border: 1px solid var(--border-subtle);">
                <div class="d-flex flex-wrap justify-content-between align-items-center pb-3 border-bottom border-secondary border-opacity-25 gap-2">
                    <div>
                        <span class="font-mono text-white fw-bold fs-6">${o.order_number}</span>
                        <span class="text-muted ms-3" style="font-size: 0.8rem;">${new Date(o.created_at).toLocaleString()}</span>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <span class="badge-status ${statusClass}">${o.status}</span>
                        <select class="form-select form-select-sm form-control-vybe" style="width: 140px; padding: 4px 8px;" onchange="updateStatus(${o.id}, this.value)">
                            <option value="">Update...</option>
                            <option value="Confirmed">Confirmed</option>
                            <option value="Processing">Processing</option>
                            <option value="Shipped">Shipped</option>
                            <option value="Delivered">Delivered</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>

                <div class="row pt-3">
                    <div class="col-md-4 mb-3 mb-md-0 border-end border-secondary border-opacity-25">
                        <div class="text-uppercase text-muted" style="font-size: 0.72rem; letter-spacing: 0.1em;">Customer & Delivery</div>
                        <div class="fw-bold text-white mt-1">${o.customer_name}</div>
                        <div class="text-muted" style="font-size: 0.82rem;">${o.customer_email} &bull; ${o.customer_phone}</div>
                        <div class="text-light mt-2" style="font-size: 0.82rem;">
                            ${o.shipping_address}, ${o.city}, ${o.state} - ${o.postal_code}
                        </div>
                    </div>

                    <div class="col-md-5 mb-3 mb-md-0 border-end border-secondary border-opacity-25">
                        <div class="text-uppercase text-muted" style="font-size: 0.72rem; letter-spacing: 0.1em;">Items Purchased</div>
                        <div class="mt-2">
                            ${(o.items || []).map(i => `
                                <div class="d-flex align-items-center gap-2 mb-2">
                                    <img src="${i.image_url || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=80&q=80'}" style="width: 32px; height: 42px; object-fit: cover;">
                                    <div style="font-size: 0.82rem;">
                                        <div class="text-white">${i.product_name}</div>
                                        <div class="text-muted">${i.size} / ${i.color} &times; ${i.quantity} = ${formatINR(i.subtotal)}</div>
                                    </div>
                                </div>
                            `).join("")}
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="text-uppercase text-muted" style="font-size: 0.72rem; letter-spacing: 0.1em;">Order Total</div>
                        <div class="fs-4 fw-bold font-mono text-white mt-1">${formatINR(o.total_amount)}</div>
                        <div class="text-muted" style="font-size: 0.78rem;">Method: ${o.payment_method}</div>
                        ${o.discount_amount > 0 ? `<div class="text-success" style="font-size: 0.78rem;">Discount: -${formatINR(o.discount_amount)}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

async function updateStatus(orderId, newStatus) {
    if (!newStatus) return;

    try {
        const res = await authFetch(`/admin/orders/${orderId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast(`Order status updated to '${newStatus}'`, "success");
            loadAdminOrders();
            loadDashboardStats();
        } else {
            showToast("Failed to update status", "danger");
        }
    } catch (e) {
        showToast("Error updating order status", "danger");
    }
}

// -----------------------------------------------------------------------------
// Products Catalog Management
// -----------------------------------------------------------------------------
async function loadAdminProducts() {
    const tableBody = document.getElementById("adminProductsTableBody");
    if (!tableBody) return;

    try {
        const res = await fetch(`${API_BASE}/products?limit=100`);
        allAdminProducts = await res.json();

        tableBody.innerHTML = allAdminProducts.map(p => `
            <tr>
                <td>
                    <img src="${p.primary_image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=80&q=80'}" style="width: 40px; height: 50px; object-fit: cover;">
                </td>
                <td>
                    <div class="fw-bold text-white">${p.name}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">${p.slug}</div>
                </td>
                <td>${p.category_name || p.gender}</td>
                <td class="font-mono">${formatINR(p.price)}</td>
                <td class="font-mono text-success">${p.discount_price ? formatINR(p.discount_price) : '-'}</td>
                <td>
                    <span class="badge ${p.in_stock ? 'bg-success' : 'bg-danger'}">
                        ${p.in_stock ? 'In Stock' : 'Out of Stock'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger py-1 px-2" onclick="deactivateProduct(${p.id}, '${p.name}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-danger text-center">Failed to load products.</td></tr>`;
    }
}

async function deactivateProduct(id, name) {
    if (!confirm(`Are you sure you want to deactivate '${name}'?`)) return;

    try {
        const res = await authFetch(`/products/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast(`Product '${name}' deactivated.`, "success");
            loadAdminProducts();
            loadDashboardStats();
        } else {
            showToast("Failed to delete product.", "danger");
        }
    } catch (e) {
        showToast("Error deleting product.", "danger");
    }
}

async function loadCategoriesDropdown() {
    const select = document.getElementById("newProdCategory");
    if (!select) return;

    try {
        const res = await fetch(`${API_BASE}/categories`);
        const cats = await res.json();
        select.innerHTML = cats.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    } catch (e) {
        console.warn("Failed to load category list", e);
    }
}

async function handleCreateProduct(e) {
    e.preventDefault();

    const name = document.getElementById("newProdName").value.trim();
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)+/g, "");
    const category_id = parseInt(document.getElementById("newProdCategory").value);
    const gender = document.getElementById("newProdGender").value;
    const price = parseFloat(document.getElementById("newProdPrice").value);
    const discount_price_val = document.getElementById("newProdDiscount").value;
    const discount_price = discount_price_val ? parseFloat(discount_price_val) : null;
    const description = document.getElementById("newProdDescription").value.trim();
    const material_details = document.getElementById("newProdMaterial").value.trim();
    const image_url = document.getElementById("newProdImage").value.trim();
    const stock_qty = parseInt(document.getElementById("newProdStock").value) || 15;
    const color = document.getElementById("newProdColor").value.trim() || "Black";

    const payload = {
        name,
        slug,
        category_id,
        gender,
        price,
        discount_price,
        description,
        material_details,
        is_featured: document.getElementById("newProdFeatured").checked,
        is_trending: document.getElementById("newProdTrending").checked,
        is_new_arrival: true,
        images: [
            { image_url, is_primary: true, display_order: 0 }
        ],
        variants: ["S", "M", "L", "XL"].map(size => ({
            size,
            color,
            stock_quantity: stock_qty,
            sku: `VYBE-${slug.slice(0, 5).toUpperCase()}-${size}-${color.slice(0, 3).toUpperCase()}`
        }))
    };

    try {
        const res = await authFetch("/products", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast(`Product '${name}' created with size variants!`, "success");
            const modalEl = document.getElementById("addProductModal");
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            document.getElementById("addProductForm").reset();
            loadAdminProducts();
            loadDashboardStats();
        } else {
            const data = await res.json();
            showToast(data.detail || "Error creating product.", "danger");
        }
    } catch (e) {
        showToast("Network error creating product.", "danger");
    }
}

// -----------------------------------------------------------------------------
// Coupons Management
// -----------------------------------------------------------------------------
async function loadAdminCoupons() {
    const container = document.getElementById("adminCouponsList");
    if (!container) return;

    try {
        const res = await authFetch("/admin/coupons");
        const coupons = await res.json();

        container.innerHTML = coupons.map(c => `
            <div class="col-md-4 mb-3">
                <div class="p-3" style="background: var(--bg-surface); border: 1px solid var(--border-subtle);">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fs-5 fw-bold font-mono text-warning">${c.code}</span>
                        <button class="btn btn-sm btn-link text-danger p-0" onclick="deleteCoupon(${c.id}, '${c.code}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                    <div class="text-light" style="font-size: 0.85rem;">
                        ${c.discount_percent ? `${c.discount_percent}% OFF` : `Flat ${formatINR(c.discount_amount)} OFF`}
                    </div>
                    <div class="text-muted" style="font-size: 0.78rem;">
                        Min Order: ${formatINR(c.min_purchase)} &bull; Used: ${c.times_used} times
                    </div>
                </div>
            </div>
        `).join("");
    } catch (e) {
        container.innerHTML = `<div class="text-danger">Failed to load coupons.</div>`;
    }
}

async function handleCreateCoupon(e) {
    e.preventDefault();
    const code = document.getElementById("newCouponCode").value.trim().toUpperCase();
    const type = document.getElementById("newCouponType").value;
    const value = parseFloat(document.getElementById("newCouponValue").value);
    const min_purchase = parseFloat(document.getElementById("newCouponMin").value) || 0;

    const payload = {
        code,
        min_purchase,
        discount_percent: type === "percent" ? value : null,
        discount_amount: type === "amount" ? value : null,
        is_active: true
    };

    try {
        const res = await authFetch("/admin/coupons", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToast(`Coupon '${code}' created!`, "success");
            const modalEl = document.getElementById("addCouponModal");
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            document.getElementById("addCouponForm").reset();
            loadAdminCoupons();
        } else {
            showToast("Failed to create coupon.", "danger");
        }
    } catch (e) {
        showToast("Error creating coupon.", "danger");
    }
}

async function deleteCoupon(id, code) {
    if (!confirm(`Delete coupon '${code}'?`)) return;
    try {
        const res = await authFetch(`/admin/coupons/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast(`Coupon deleted.`, "info");
            loadAdminCoupons();
        }
    } catch (e) {
        showToast("Error deleting coupon.", "danger");
    }
}

function setupAdminTabs() {
    const tabs = document.querySelectorAll(".admin-nav-item");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const targetSection = tab.getAttribute("data-target");
            document.querySelectorAll(".admin-tab-pane").forEach(pane => {
                pane.style.display = pane.id === targetSection ? "block" : "none";
            });
        });
    });

    // Orders Filter & Search
    const statusFilter = document.getElementById("orderStatusFilter");
    if (statusFilter) statusFilter.addEventListener("change", renderFilteredOrders);

    const searchInput = document.getElementById("orderSearchInput");
    if (searchInput) searchInput.addEventListener("input", renderFilteredOrders);

    // Form Submissions
    const addProdForm = document.getElementById("addProductForm");
    if (addProdForm) addProdForm.addEventListener("submit", handleCreateProduct);

    const addCouponForm = document.getElementById("addCouponForm");
    if (addCouponForm) addCouponForm.addEventListener("submit", handleCreateCoupon);
}

document.addEventListener("DOMContentLoaded", () => {
    initAdminDashboard();
});
