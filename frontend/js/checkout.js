/**
 * VYBE CLOTHING - SECURE CHECKOUT FLOW (checkout.js)
 */

let checkoutCoupon = null;

async function initCheckoutPage() {
    const form = document.getElementById("checkoutForm");
    if (!form) return;

    const cart = getCart();
    if (cart.length === 0) {
        showToast("Your shopping bag is empty. Redirecting to shop...", "info");
        setTimeout(() => { window.location.href = "shop.html"; }, 1500);
        return;
    }

    // Retrieve saved coupon
    const savedCoupon = sessionStorage.getItem("vybe_applied_coupon");
    if (savedCoupon) {
        try { checkoutCoupon = JSON.parse(savedCoupon); } catch (e) { checkoutCoupon = null; }
    }

    renderCheckoutSummary(cart);
    prefillUserData();
    setupCheckoutForm();
}

function renderCheckoutSummary(cart) {
    const itemsList = document.getElementById("checkoutItemsList");
    if (!itemsList) return;

    itemsList.innerHTML = cart.map(item => `
        <div class="d-flex align-items-center gap-3 mb-3 pb-3 border-bottom border-secondary border-opacity-25">
            <img src="${item.image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=150&q=80'}" alt="${item.name}" style="width: 55px; height: 70px; object-fit: cover; border: 1px solid var(--border-subtle);">
            <div class="flex-grow-1">
                <h6 class="mb-1 text-white" style="font-size: 0.9rem;">${item.name}</h6>
                <div class="text-muted" style="font-size: 0.78rem;">
                    Size: <span class="text-white">${item.size}</span> &nbsp;|&nbsp; Color: <span class="text-white">${item.color}</span> &nbsp;|&nbsp; Qty: ${item.quantity}
                </div>
            </div>
            <div class="text-white font-mono fw-bold" style="font-size: 0.95rem;">
                ${formatINR(item.price * item.quantity)}
            </div>
        </div>
    `).join("");

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const shippingFee = subtotal >= 1999.0 ? 0.0 : 150.0;
    const discount = checkoutCoupon ? (checkoutCoupon.discount_amount || 0.0) : 0.0;
    const total = Math.max(0, subtotal - discount + shippingFee);

    document.getElementById("checkoutSubtotal").textContent = formatINR(subtotal);
    document.getElementById("checkoutShipping").textContent = shippingFee === 0 ? "FREE" : formatINR(shippingFee);
    
    const discountRow = document.getElementById("checkoutDiscountRow");
    if (discount > 0) {
        discountRow.style.display = "flex";
        document.getElementById("checkoutDiscount").textContent = `-${formatINR(discount)}`;
        document.getElementById("checkoutCouponLabel").textContent = `Coupon (${checkoutCoupon.code})`;
    } else {
        discountRow.style.display = "none";
    }

    document.getElementById("checkoutTotal").textContent = formatINR(total);
}

async function prefillUserData() {
    const user = getCurrentUser();
    if (!user) return;

    const nameInput = document.getElementById("custName");
    const emailInput = document.getElementById("custEmail");
    const phoneInput = document.getElementById("custPhone");

    if (nameInput) nameInput.value = user.full_name || "";
    if (emailInput) {
        emailInput.value = user.email || "";
        emailInput.readOnly = true;
    }
    if (phoneInput && user.phone) phoneInput.value = user.phone;

    // Load saved addresses
    try {
        const res = await authFetch("/auth/addresses");
        if (res.ok) {
            const addresses = await res.json();
            renderSavedAddressesSelector(addresses);
        }
    } catch (e) {
        console.warn("Addresses load failed", e);
    }
}

function renderSavedAddressesSelector(addresses) {
    const container = document.getElementById("savedAddressesContainer");
    if (!container || addresses.length === 0) return;

    container.style.display = "block";
    const select = document.getElementById("savedAddressSelect");
    select.innerHTML = `<option value="">-- Choose a saved address --</option>` + 
        addresses.map((a, idx) => `
            <option value="${a.id}" data-addr='${JSON.stringify(a)}' ${a.is_default ? 'selected' : ''}>
                ${a.full_name} - ${a.street_address}, ${a.city} (${a.postal_code})
            </option>
        `).join("");

    select.addEventListener("change", () => {
        const selectedOpt = select.options[select.selectedIndex];
        if (!selectedOpt || !selectedOpt.dataset.addr) return;
        const addr = JSON.parse(selectedOpt.dataset.addr);
        document.getElementById("custName").value = addr.full_name;
        document.getElementById("custPhone").value = addr.phone;
        document.getElementById("custAddress").value = addr.street_address;
        document.getElementById("custCity").value = addr.city;
        document.getElementById("custState").value = addr.state;
        document.getElementById("custPostal").value = addr.postal_code;
    });

    // Auto-fill default address
    const defaultAddr = addresses.find(a => a.is_default);
    if (defaultAddr) {
        document.getElementById("custAddress").value = defaultAddr.street_address;
        document.getElementById("custCity").value = defaultAddr.city;
        document.getElementById("custState").value = defaultAddr.state;
        document.getElementById("custPostal").value = defaultAddr.postal_code;
    }
}

function setupCheckoutForm() {
    const form = document.getElementById("checkoutForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const btn = document.getElementById("placeOrderBtn");
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span> PLACING ORDER...`;

        const cart = getCart();
        if (cart.length === 0) {
            showToast("Your cart is empty.", "danger");
            btn.disabled = false;
            btn.textContent = "COMPLETE ORDER (COD)";
            return;
        }

        const payload = {
            customer_name: document.getElementById("custName").value.trim(),
            customer_email: document.getElementById("custEmail").value.trim(),
            customer_phone: document.getElementById("custPhone").value.trim(),
            shipping_address: document.getElementById("custAddress").value.trim(),
            city: document.getElementById("custCity").value.trim(),
            state: document.getElementById("custState").value.trim(),
            postal_code: document.getElementById("custPostal").value.trim(),
            country: "India",
            payment_method: "COD",
            coupon_code: checkoutCoupon ? checkoutCoupon.code : null,
            notes: document.getElementById("orderNotes") ? document.getElementById("orderNotes").value.trim() : null,
            items: cart.map(i => ({
                product_id: i.productId,
                size: i.size,
                color: i.color,
                quantity: i.quantity
            }))
        };

        try {
            const res = await authFetch("/orders", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok) {
                // Clear cart & applied coupon
                localStorage.removeItem("vybe_cart");
                sessionStorage.removeItem("vybe_applied_coupon");
                updateCartCount();

                // Render confirmation state
                renderOrderConfirmation(data);
            } else {
                showToast(data.detail || "Failed to process order. Please check inputs.", "danger");
                btn.disabled = false;
                btn.textContent = "COMPLETE ORDER (COD)";
            }
        } catch (err) {
            showToast("Network error. Please try again.", "danger");
            btn.disabled = false;
            btn.textContent = "COMPLETE ORDER (COD)";
        }
    });
}

function renderOrderConfirmation(order) {
    const checkoutContainer = document.getElementById("checkoutContainer");
    if (!checkoutContainer) return;

    checkoutContainer.innerHTML = `
        <div class="row justify-content-center py-5">
            <div class="col-12 col-lg-8">
                <div class="p-4 p-md-5 text-center" style="background: var(--bg-surface); border: 1px solid var(--border-subtle);">
                    <div class="mb-4">
                        <i class="bi bi-check-circle-fill text-success" style="font-size: 4rem;"></i>
                    </div>
                    <span class="tracking-widest-custom text-success fw-bold" style="font-size: 0.85rem;">ORDER CONFIRMED</span>
                    <h2 class="text-uppercase fw-bold mt-2 mb-3">THANK YOU FOR YOUR ORDER</h2>
                    <p class="text-muted" style="max-width: 500px; margin: 0 auto 24px;">
                        We've received your order and our fulfillment team is preparing it for dispatch. A confirmation notification has been sent to <strong>${order.customer_email}</strong>.
                    </p>

                    <div class="p-3 mb-4 mx-auto font-mono text-center" style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); max-width: 400px;">
                        <div class="text-muted" style="font-size: 0.75rem;">ORDER TRACKING NUMBER</div>
                        <div class="fs-4 fw-bold text-white mt-1">${order.order_number}</div>
                    </div>

                    <div class="row text-start p-3 mb-4" style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle);">
                        <div class="col-md-6 mb-3 mb-md-0">
                            <h6 class="text-uppercase text-muted" style="font-size: 0.75rem;">Delivery Destination</h6>
                            <div class="text-white fw-bold">${order.customer_name}</div>
                            <div class="text-muted" style="font-size: 0.85rem;">
                                ${order.shipping_address}<br>
                                ${order.city}, ${order.state} - ${order.postal_code}
                            </div>
                            <div class="text-muted" style="font-size: 0.85rem;">Phone: ${order.customer_phone}</div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-uppercase text-muted" style="font-size: 0.75rem;">Payment & Total</h6>
                            <div class="text-white fw-bold">Cash on Delivery (COD)</div>
                            <div class="fs-5 fw-bold font-mono text-white mt-2">${formatINR(order.total_amount)}</div>
                            <span class="badge bg-warning text-dark mt-1">Pending at Doorstep</span>
                        </div>
                    </div>

                    <div class="d-flex flex-wrap justify-content-center gap-3">
                        <a href="/orders.html" class="btn btn-vybe">
                            <i class="bi bi-box-seam me-2"></i> TRACK IN MY ORDERS
                        </a>
                        <a href="shop.html" class="btn btn-vybe-outline">
                            CONTINUE SHOPPING
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    window.scrollTo({ top: 0, behavior: "smooth" });
}

document.addEventListener("DOMContentLoaded", () => {
    initCheckoutPage();
});
