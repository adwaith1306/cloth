/**
 * VYBE CLOTHING - SHOPPING CART LOGIC (cart.js)
 */

const FREE_SHIPPING_THRESHOLD = 1999.0;
const STANDARD_SHIPPING_FEE = 150.0;

let appliedCoupon = null;

function initCartPage() {
    const cartItemsContainer = document.getElementById("cartItemsContainer");
    if (!cartItemsContainer) return;

    // Retrieve saved coupon if any
    const savedCoupon = sessionStorage.getItem("vybe_applied_coupon");
    if (savedCoupon) {
        try {
            appliedCoupon = JSON.parse(savedCoupon);
        } catch (e) {
            appliedCoupon = null;
        }
    }

    renderCart();
    setupCouponForm();
}

function renderCart() {
    const cart = getCart();
    const itemsContainer = document.getElementById("cartItemsContainer");
    const emptyState = document.getElementById("cartEmptyState");
    const mainContent = document.getElementById("cartMainContent");

    if (!itemsContainer) return;

    if (cart.length === 0) {
        if (emptyState) emptyState.style.display = "block";
        if (mainContent) mainContent.style.display = "none";
        return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (mainContent) mainContent.style.display = "flex";

    // Render items list
    itemsContainer.innerHTML = cart.map((item, index) => {
        const itemSubtotal = item.price * item.quantity;
        return `
            <div class="cart-item-row">
                <img src="${item.image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=300&q=80'}" alt="${item.name}" class="cart-item-img">
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="fw-bold mb-1" style="font-size: 1.05rem;">
                                <a href="/product.html?slug=${item.slug}" class="text-white text-decoration-none">${item.name}</a>
                            </h5>
                            <div class="text-muted mb-2" style="font-size: 0.85rem;">
                                Size: <span class="text-white font-mono">${item.size}</span> &nbsp;|&nbsp; Color: <span class="text-white">${item.color}</span>
                            </div>
                            <div class="fw-bold font-mono text-light">${formatINR(item.price)}</div>
                        </div>
                        <button class="btn btn-link text-muted p-0" onclick="removeCartItem(${index})" title="Remove">
                            <i class="bi bi-trash3" style="font-size: 1.15rem;"></i>
                        </button>
                    </div>

                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <div class="qty-counter">
                            <button type="button" onclick="updateCartItemQty(${index}, -1)">-</button>
                            <input type="text" value="${item.quantity}" readonly>
                            <button type="button" onclick="updateCartItemQty(${index}, 1)">+</button>
                        </div>
                        <div class="font-mono fw-bold text-white fs-6">
                            ${formatINR(itemSubtotal)}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    updateCartSummary(cart);
}

function updateCartItemQty(index, delta) {
    const cart = getCart();
    if (!cart[index]) return;

    const newQty = cart[index].quantity + delta;

    if (newQty <= 0) {
        removeCartItem(index);
        return;
    }

    if (cart[index].maxStock && newQty > cart[index].maxStock) {
        showToast(`Maximum available stock is ${cart[index].maxStock}`, "info");
        return;
    }

    cart[index].quantity = newQty;
    saveCart(cart);
    renderCart();

    // Revalidate coupon if subtotal changed
    if (appliedCoupon) {
        revalidateAppliedCoupon();
    }
}

function removeCartItem(index) {
    const cart = getCart();
    if (!cart[index]) return;

    const removedName = cart[index].name;
    cart.splice(index, 1);
    saveCart(cart);
    renderCart();
    showToast(`Removed '${removedName}' from bag.`, "info");

    if (cart.length === 0) {
        removeCoupon();
    } else if (appliedCoupon) {
        revalidateAppliedCoupon();
    }
}

function updateCartSummary(cart) {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    // Free shipping calculation
    const shippingProgressBox = document.getElementById("shippingProgressBox");
    const shippingProgressBar = document.getElementById("shippingProgressBar");
    const shippingProgressText = document.getElementById("shippingProgressText");

    let shippingFee = 0.0;
    if (subtotal >= FREE_SHIPPING_THRESHOLD) {
        shippingFee = 0.0;
        if (shippingProgressBox) {
            shippingProgressBar.style.width = "100%";
            shippingProgressBar.classList.remove("bg-warning");
            shippingProgressBar.classList.add("bg-success");
            shippingProgressText.innerHTML = `<i class="bi bi-check-circle-fill text-success me-1"></i> You've unlocked <strong>FREE Express Shipping</strong>!`;
        }
    } else {
        shippingFee = STANDARD_SHIPPING_FEE;
        const diff = FREE_SHIPPING_THRESHOLD - subtotal;
        const pct = Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100);
        if (shippingProgressBox) {
            shippingProgressBar.style.width = `${pct}%`;
            shippingProgressBar.classList.remove("bg-success");
            shippingProgressBar.classList.add("bg-warning");
            shippingProgressText.innerHTML = `Add <strong>${formatINR(diff)}</strong> more to get <strong>FREE Express Shipping</strong>!`;
        }
    }

    // Coupon discount
    let discount = 0.0;
    if (appliedCoupon && appliedCoupon.discount_amount) {
        discount = appliedCoupon.discount_amount;
    }

    const total = Math.max(0, subtotal - discount + shippingFee);

    // Update DOM
    if (document.getElementById("summarySubtotal")) {
        document.getElementById("summarySubtotal").textContent = formatINR(subtotal);
    }
    if (document.getElementById("summaryShipping")) {
        document.getElementById("summaryShipping").textContent = shippingFee === 0 ? "FREE" : formatINR(shippingFee);
    }
    if (document.getElementById("summaryDiscount")) {
        const discountRow = document.getElementById("summaryDiscountRow");
        if (discount > 0) {
            discountRow.style.display = "flex";
            document.getElementById("summaryDiscount").textContent = `-${formatINR(discount)}`;
        } else {
            discountRow.style.display = "none";
        }
    }
    if (document.getElementById("summaryTotal")) {
        document.getElementById("summaryTotal").textContent = formatINR(total);
    }
}

function setupCouponForm() {
    const form = document.getElementById("couponForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("couponInput");
        const code = input.value.trim().toUpperCase();

        if (!code) {
            showToast("Please enter a promo code.", "info");
            return;
        }

        const cart = getCart();
        const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        try {
            const res = await fetch(`${API_BASE}/orders/validate-coupon`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, subtotal })
            });

            const data = await res.json();
            if (data.valid) {
                appliedCoupon = { code: data.code, discount_amount: data.discount_amount };
                sessionStorage.setItem("vybe_applied_coupon", JSON.stringify(appliedCoupon));
                showToast(data.message, "success");
                renderAppliedCouponBadge();
                renderCart();
            } else {
                showToast(data.message || "Invalid coupon.", "danger");
            }
        } catch (err) {
            showToast("Error checking coupon code.", "danger");
        }
    });

    renderAppliedCouponBadge();
}

function renderAppliedCouponBadge() {
    const badgeContainer = document.getElementById("appliedCouponBadge");
    if (!badgeContainer) return;

    if (appliedCoupon && appliedCoupon.code) {
        badgeContainer.style.display = "flex";
        badgeContainer.innerHTML = `
            <div class="d-flex align-items-center justify-content-between p-2 mt-2 w-100" style="background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3); font-size: 0.85rem;">
                <div>
                    <i class="bi bi-tag-fill text-success me-2"></i>
                    <strong>${appliedCoupon.code}</strong> applied (-${formatINR(appliedCoupon.discount_amount)})
                </div>
                <button class="btn btn-sm btn-link text-muted p-0 text-decoration-none" onclick="removeCoupon()">
                    <i class="bi bi-x-circle-fill"></i>
                </button>
            </div>
        `;
    } else {
        badgeContainer.style.display = "none";
        badgeContainer.innerHTML = "";
    }
}

async function revalidateAppliedCoupon() {
    if (!appliedCoupon) return;
    const cart = getCart();
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    try {
        const res = await fetch(`${API_BASE}/orders/validate-coupon`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: appliedCoupon.code, subtotal })
        });
        const data = await res.json();
        if (data.valid) {
            appliedCoupon.discount_amount = data.discount_amount;
            sessionStorage.setItem("vybe_applied_coupon", JSON.stringify(appliedCoupon));
            renderAppliedCouponBadge();
            updateCartSummary(cart);
        } else {
            removeCoupon();
            showToast(`Coupon removed: ${data.message}`, "info");
        }
    } catch (e) {
        console.warn("Coupon revalidation failed", e);
    }
}

function removeCoupon() {
    appliedCoupon = null;
    sessionStorage.removeItem("vybe_applied_coupon");
    renderAppliedCouponBadge();
    const input = document.getElementById("couponInput");
    if (input) input.value = "";
    renderCart();
}

function proceedToCheckout() {
    const cart = getCart();
    if (cart.length === 0) {
        showToast("Your bag is empty.", "info");
        return;
    }
    window.location.href = "/checkout.html";
}

document.addEventListener("DOMContentLoaded", () => {
    initCartPage();
});
