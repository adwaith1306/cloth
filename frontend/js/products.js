/**
 * VYBE CLOTHING - PRODUCTS & CATALOG ENGINE (products.js)
 */

// Helper to generate a single Product Card HTML string
function renderProductCardHTML(p) {
    const hasDiscount = p.discount_price && p.discount_price < p.price;
    const discountPercent = hasDiscount ? Math.round(((p.price - p.discount_price) / p.price) * 100) : 0;
    
    // Tag badge
    let badgeHTML = "";
    if (p.is_new_arrival) {
        badgeHTML = `<span class="badge-tag badge-new">NEW DROP</span>`;
    } else if (hasDiscount) {
        badgeHTML = `<span class="badge-tag badge-sale">${discountPercent}% OFF</span>`;
    } else if (p.is_trending) {
        badgeHTML = `<span class="badge-tag badge-trending">TRENDING</span>`;
    }

    // Sizes pills
    const sizesHTML = (p.available_sizes || []).slice(0, 4).map(s => 
        `<span class="size-pill-sm">${s}</span>`
    ).join("");

    return `
        <div class="col-6 col-md-4 col-lg-3 mb-4">
            <div class="product-card">
                <a href="/product.html?slug=${p.slug}" class="product-img-wrapper d-block">
                    ${badgeHTML}
                    <img src="${p.primary_image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80'}" alt="${p.name}" loading="lazy">
                </a>
                <div class="product-card-body">
                    <div class="product-card-category">${p.category_name || p.gender}</div>
                    <a href="/product.html?slug=${p.slug}" class="product-card-title text-decoration-none" title="${p.name}">
                        ${p.name}
                    </a>
                    
                    <div class="size-preview-pills mt-1">
                        ${sizesHTML}
                    </div>

                    <div class="product-price-row">
                        <span class="current-price">${formatINR(hasDiscount ? p.discount_price : p.price)}</span>
                        ${hasDiscount ? `<span class="original-price">${formatINR(p.price)}</span>` : ''}
                    </div>

                    <a href="/product.html?slug=${p.slug}" class="btn btn-vybe-dark w-100 mt-2 py-2 text-center text-decoration-none" style="font-size: 0.75rem;">
                        SELECT SIZE & BUY
                    </a>
                </div>
            </div>
        </div>
    `;
}

// -----------------------------------------------------------------------------
// Homepage Sections Loader (Featured & New Drops)
// -----------------------------------------------------------------------------
async function loadHomeProducts() {
    const featuredContainer = document.getElementById("homeFeaturedGrid");
    const trendingContainer = document.getElementById("homeTrendingGrid");

    if (featuredContainer) {
        try {
            const res = await fetch(`${API_BASE}/products/featured?limit=4`);
            const products = await res.json();
            featuredContainer.innerHTML = products.map(renderProductCardHTML).join("");
        } catch (err) {
            featuredContainer.innerHTML = `<p class="text-muted">Unable to load featured products.</p>`;
        }
    }

    if (trendingContainer) {
        try {
            const res = await fetch(`${API_BASE}/products/trending?limit=4`);
            const products = await res.json();
            trendingContainer.innerHTML = products.map(renderProductCardHTML).join("");
        } catch (err) {
            trendingContainer.innerHTML = `<p class="text-muted">Unable to load trending products.</p>`;
        }
    }
}

// -----------------------------------------------------------------------------
// Shop Catalog Page Controller
// -----------------------------------------------------------------------------
async function initShopPage() {
    const grid = document.getElementById("shopProductGrid");
    if (!grid) return;

    // Parse URL Params
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get("category") || "";
    const genderParam = urlParams.get("gender") || "";
    const searchParam = urlParams.get("q") || "";
    const sortParam = urlParams.get("sort") || "newest";

    // Set UI inputs if matching
    if (document.getElementById("shopSearchInput") && searchParam) {
        document.getElementById("shopSearchInput").value = searchParam;
    }
    if (document.getElementById("sortSelector") && sortParam) {
        document.getElementById("sortSelector").value = sortParam;
    }

    // Load Categories Filter List
    loadShopCategories(categoryParam);

    // Initial Fetch
    fetchShopProducts();

    // Event Listeners for Filters
    setupShopEventListeners();
}

async function loadShopCategories(activeCategorySlug) {
    const container = document.getElementById("categoryFilterList");
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/categories`);
        const categories = await res.json();
        
        let html = `
            <div class="filter-pill mb-2 ${!activeCategorySlug ? 'active' : ''}" data-category="">
                All Collections
            </div>
        `;

        categories.forEach(cat => {
            const isActive = cat.slug === activeCategorySlug ? 'active' : '';
            html += `
                <div class="filter-pill mb-2 d-flex justify-content-between align-items-center ${isActive}" data-category="${cat.slug}">
                    <span>${cat.name}</span>
                    <span style="font-size: 0.7rem; opacity: 0.7;">(${cat.product_count})</span>
                </div>
            `;
        });

        container.innerHTML = html;

        // Click listeners on category pills
        container.querySelectorAll(".filter-pill").forEach(pill => {
            pill.addEventListener("click", () => {
                container.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
                pill.classList.add("active");
                fetchShopProducts();
            });
        });

    } catch (e) {
        console.error("Failed to load categories:", e);
    }
}

async function fetchShopProducts() {
    const grid = document.getElementById("shopProductGrid");
    const countDisplay = document.getElementById("productCountDisplay");
    if (!grid) return;

    grid.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-light" role="status"></div>
            <p class="mt-3 text-muted" style="letter-spacing: 0.1em;">CURATING COLLECTION...</p>
        </div>
    `;

    // Gather active filters
    const activeCategoryPill = document.querySelector("#categoryFilterList .filter-pill.active");
    const category = activeCategoryPill ? activeCategoryPill.getAttribute("data-category") : "";
    
    const activeGenderPill = document.querySelector("#genderFilterList .filter-pill.active");
    const gender = activeGenderPill ? activeGenderPill.getAttribute("data-gender") : "";

    const activeSizeBtn = document.querySelector("#sizeFilterList .filter-pill.active");
    const size = activeSizeBtn ? activeSizeBtn.getAttribute("data-size") : "";

    const searchInput = document.getElementById("shopSearchInput");
    const q = searchInput ? searchInput.value.trim() : "";

    const sortSelector = document.getElementById("sortSelector");
    const sortBy = sortSelector ? sortSelector.value : "newest";

    const maxPriceInput = document.getElementById("maxPriceInput");
    const maxPrice = maxPriceInput ? maxPriceInput.value : "";

    // Build URL
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (gender) params.append("gender", gender);
    if (size) params.append("size", size);
    if (q) params.append("q", q);
    if (sortBy) params.append("sort_by", sortBy);
    if (maxPrice && maxPrice < 10000) params.append("max_price", maxPrice);

    try {
        const res = await fetch(`${API_BASE}/products?${params.toString()}`);
        const products = await res.json();

        if (countDisplay) {
            countDisplay.textContent = `Showing ${products.length} products`;
        }

        if (products.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5 my-4">
                    <i class="bi bi-search text-muted mb-3" style="font-size: 3rem;"></i>
                    <h4 class="text-uppercase fw-bold">No Products Found</h4>
                    <p class="text-muted">Try adjusting your filters or search terms.</p>
                    <button class="btn btn-vybe-outline mt-3" onclick="resetFilters()">CLEAR ALL FILTERS</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = products.map(renderProductCardHTML).join("");

    } catch (err) {
        grid.innerHTML = `
            <div class="col-12 text-center py-5 text-danger">
                Failed to load products. Please ensure the backend server is running.
            </div>
        `;
    }
}

function setupShopEventListeners() {
    // Sort selector change
    const sortSelector = document.getElementById("sortSelector");
    if (sortSelector) {
        sortSelector.addEventListener("change", fetchShopProducts);
    }

    // Gender filter pills
    document.querySelectorAll("#genderFilterList .filter-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("#genderFilterList .filter-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            fetchShopProducts();
        });
    });

    // Size filter pills
    document.querySelectorAll("#sizeFilterList .filter-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            if (pill.classList.contains("active")) {
                pill.classList.remove("active");
            } else {
                document.querySelectorAll("#sizeFilterList .filter-pill").forEach(p => p.classList.remove("active"));
                pill.classList.add("active");
            }
            fetchShopProducts();
        });
    });

    // Search bar submit/debounce
    const searchForm = document.getElementById("shopSearchForm");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            fetchShopProducts();
        });
    }

    // Price range slider
    const priceSlider = document.getElementById("maxPriceInput");
    const priceValDisplay = document.getElementById("maxPriceDisplay");
    if (priceSlider && priceValDisplay) {
        priceSlider.addEventListener("input", (e) => {
            priceValDisplay.textContent = formatINR(e.target.value);
        });
        priceSlider.addEventListener("change", fetchShopProducts);
    }
}

function resetFilters() {
    document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
    const allCat = document.querySelector("#categoryFilterList .filter-pill[data-category='']");
    if (allCat) allCat.classList.add("active");
    const allGen = document.querySelector("#genderFilterList .filter-pill[data-gender='']");
    if (allGen) allGen.classList.add("active");
    if (document.getElementById("shopSearchInput")) document.getElementById("shopSearchInput").value = "";
    if (document.getElementById("maxPriceInput")) document.getElementById("maxPriceInput").value = 10000;
    if (document.getElementById("maxPriceDisplay")) document.getElementById("maxPriceDisplay").textContent = "₹10,000";
    fetchShopProducts();
}

// -----------------------------------------------------------------------------
// Product Detail Page Controller (product.html)
// -----------------------------------------------------------------------------
let currentProduct = null;
let selectedSize = null;
let selectedColor = null;

async function initProductDetailPage() {
    const container = document.getElementById("productDetailContainer");
    if (!container) return;

    const urlParams = new URLSearchParams(window.location.search);
    const slug = urlParams.get("slug") || urlParams.get("id");

    if (!slug) {
        window.location.href = "shop.html";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/products/${slug}`);
        if (!res.status === 200 || !res.ok) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <h3 class="text-uppercase fw-bold">Product Not Found</h3>
                    <a href="shop.html" class="btn btn-vybe mt-3">RETURN TO SHOP</a>
                </div>
            `;
            return;
        }

        currentProduct = await res.json();
        renderProductDetailView(currentProduct);
        loadRelatedProducts(currentProduct.category_id, currentProduct.id);

    } catch (e) {
        container.innerHTML = `<div class="text-danger py-5">Failed to fetch product details.</div>`;
    }
}

function renderProductDetailView(p) {
    document.title = `${p.name} | VYBE Clothing`;

    // Breadcrumb
    const breadcrumbName = document.getElementById("breadcrumbProductName");
    if (breadcrumbName) breadcrumbName.textContent = p.name;

    // Gallery
    const mainImg = document.getElementById("productMainImage");
    if (mainImg) mainImg.src = p.primary_image;

    const thumbContainer = document.getElementById("productThumbnails");
    if (thumbContainer && p.images && p.images.length > 0) {
        thumbContainer.innerHTML = p.images.map((img, idx) => `
            <div class="thumbnail-box ${idx === 0 ? 'active' : ''}" onclick="switchProductImage('${img.image_url}', this)">
                <img src="${img.image_url}" alt="thumbnail">
            </div>
        `).join("");
    }

    // Title, category, price
    document.getElementById("productTitle").textContent = p.name;
    document.getElementById("productCategoryBadge").textContent = `${p.gender} • ${p.category_name || 'STREETWEAR'}`;
    
    const hasDiscount = p.discount_price && p.discount_price < p.price;
    const effPrice = hasDiscount ? p.discount_price : p.price;
    document.getElementById("productCurrentPrice").textContent = formatINR(effPrice);
    
    if (hasDiscount) {
        const origElem = document.getElementById("productOriginalPrice");
        origElem.textContent = formatINR(p.price);
        origElem.style.display = "inline";
        const discBadge = document.getElementById("productDiscountPercent");
        const pct = Math.round(((p.price - p.discount_price) / p.price) * 100);
        discBadge.textContent = `${pct}% OFF`;
        discBadge.style.display = "inline";
    }

    // Rating
    document.getElementById("productRatingScore").textContent = p.rating.toFixed(1);
    document.getElementById("productReviewCount").textContent = `(${p.review_count} reviews)`;

    // Description & specs
    document.getElementById("productDescription").textContent = p.description;
    if (p.material_details && document.getElementById("productMaterialDetails")) {
        document.getElementById("productMaterialDetails").textContent = p.material_details;
    }

    // Render Color selector
    const colors = listDistinctColors(p.variants);
    const colorContainer = document.getElementById("productColorsContainer");
    if (colorContainer) {
        selectedColor = colors[0] || "Black";
        colorContainer.innerHTML = colors.map((col, idx) => `
            <button class="color-swatch-btn ${idx === 0 ? 'active' : ''}" onclick="selectProductColor('${col}', this)">
                <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:#fff; border:1px solid #999;"></span>
                <span>${col}</span>
            </button>
        `).join("");
    }

    // Render Size selector
    renderSizesForColor(selectedColor);

    // Render Reviews
    renderProductReviews(p.reviews || []);
}

function switchProductImage(url, element) {
    const mainImg = document.getElementById("productMainImage");
    if (mainImg) mainImg.src = url;
    document.querySelectorAll(".thumbnail-box").forEach(t => t.classList.remove("active"));
    if (element) element.classList.add("active");
}

function listDistinctColors(variants = []) {
    return Array.from(new Set(variants.map(v => v.color)));
}

function selectProductColor(color, element) {
    selectedColor = color;
    document.querySelectorAll(".color-swatch-btn").forEach(b => b.classList.remove("active"));
    if (element) element.classList.add("active");
    renderSizesForColor(color);
}

function renderSizesForColor(color) {
    const sizeContainer = document.getElementById("productSizesContainer");
    const stockStatus = document.getElementById("productStockStatus");
    if (!sizeContainer) return;

    // Filter variants by color
    const matchingVariants = currentProduct.variants.filter(v => v.color.toLowerCase() === color.toLowerCase());

    if (matchingVariants.length === 0) {
        sizeContainer.innerHTML = `<span class="text-danger">No sizes available for ${color}</span>`;
        return;
    }

    // Default select first available size
    const availableVariant = matchingVariants.find(v => v.stock_quantity > 0) || matchingVariants[0];
    selectedSize = availableVariant.size;

    sizeContainer.innerHTML = matchingVariants.map(v => {
        const isOutOfStock = v.stock_quantity <= 0;
        const isSelected = v.size === selectedSize;
        return `
            <button 
                class="size-btn ${isSelected ? 'active' : ''} ${isOutOfStock ? 'disabled' : ''}" 
                ${isOutOfStock ? 'disabled' : ''}
                onclick="selectProductSize('${v.size}', ${v.stock_quantity}, this)">
                ${v.size}
            </button>
        `;
    }).join("");

    updateStockIndicator(availableVariant.stock_quantity);
}

function selectProductSize(size, stockQty, element) {
    selectedSize = size;
    document.querySelectorAll(".size-btn").forEach(b => b.classList.remove("active"));
    if (element) element.classList.add("active");
    updateStockIndicator(stockQty);

    // Reset qty if current qty > stock
    const qtyInput = document.getElementById("productQuantityInput");
    if (qtyInput && parseInt(qtyInput.value) > stockQty) {
        qtyInput.value = Math.max(1, stockQty);
    }
}

function updateStockIndicator(stockQty) {
    const stockStatus = document.getElementById("productStockStatus");
    if (!stockStatus) return;

    if (stockQty <= 0) {
        stockStatus.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-x-circle me-1"></i> Out of Stock</span>`;
    } else if (stockQty <= 5) {
        stockStatus.innerHTML = `<span class="text-warning fw-bold"><i class="bi bi-exclamation-triangle me-1"></i> Only ${stockQty} items left in stock — order soon!</span>`;
    } else {
        stockStatus.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-check-circle me-1"></i> In Stock & Ready to Ship</span>`;
    }
}

function adjustDetailQty(delta) {
    const input = document.getElementById("productQuantityInput");
    if (!input) return;

    let current = parseInt(input.value) || 1;
    let next = current + delta;
    if (next < 1) next = 1;

    // Check max stock for selected variant
    if (currentProduct && selectedSize && selectedColor) {
        const v = currentProduct.variants.find(
            varItem => varItem.size.toLowerCase() === selectedSize.toLowerCase() &&
                       varItem.color.toLowerCase() === selectedColor.toLowerCase()
        );
        if (v && next > v.stock_quantity) {
            showToast(`Cannot add more than ${v.stock_quantity} available units.`, "info");
            return;
        }
    }

    input.value = next;
}

// Add to Cart handler on detail page
function handleAddToCartDetail(isBuyNow = false) {
    if (!currentProduct || !selectedSize || !selectedColor) {
        showToast("Please select your size and color.", "info");
        return;
    }

    const matchingVariant = currentProduct.variants.find(
        v => v.size.toLowerCase() === selectedSize.toLowerCase() &&
             v.color.toLowerCase() === selectedColor.toLowerCase()
    );

    if (!matchingVariant || matchingVariant.stock_quantity <= 0) {
        showToast("Selected size is currently out of stock.", "danger");
        return;
    }

    const qty = parseInt(document.getElementById("productQuantityInput").value) || 1;
    if (qty > matchingVariant.stock_quantity) {
        showToast(`Only ${matchingVariant.stock_quantity} units available.`, "danger");
        return;
    }

    const effectivePrice = currentProduct.discount_price && currentProduct.discount_price < currentProduct.price 
        ? currentProduct.discount_price 
        : currentProduct.price;

    const cart = getCart();
    const itemKey = `${currentProduct.id}_${selectedSize}_${selectedColor}`;
    const existingIndex = cart.findIndex(item => `${item.productId}_${item.size}_${item.color}` === itemKey);

    if (existingIndex > -1) {
        const newTotal = cart[existingIndex].quantity + qty;
        if (newTotal > matchingVariant.stock_quantity) {
            showToast(`Cannot exceed total available stock (${matchingVariant.stock_quantity}).`, "danger");
            return;
        }
        cart[existingIndex].quantity = newTotal;
    } else {
        cart.push({
            productId: currentProduct.id,
            name: currentProduct.name,
            slug: currentProduct.slug,
            image: currentProduct.primary_image,
            size: selectedSize,
            color: selectedColor,
            price: effectivePrice,
            quantity: qty,
            maxStock: matchingVariant.stock_quantity
        });
    }

    saveCart(cart);
    showToast(`Added ${qty}x '${currentProduct.name}' (${selectedSize}) to bag!`, "success");

    if (isBuyNow) {
        window.location.href = "/checkout.html";
    }
}

// -----------------------------------------------------------------------------
// Reviews
// -----------------------------------------------------------------------------
function renderProductReviews(reviews) {
    const list = document.getElementById("reviewsListContainer");
    if (!list) return;

    if (reviews.length === 0) {
        list.innerHTML = `<p class="text-muted">No reviews yet. Be the first to share your thoughts!</p>`;
        return;
    }

    list.innerHTML = reviews.map(r => `
        <div class="p-3 mb-3" style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle);">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <span class="text-warning me-2">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                    <strong class="text-light">${r.title || 'Verified Purchase'}</strong>
                </div>
                <span class="text-muted" style="font-size: 0.78rem;">${new Date(r.created_at).toLocaleDateString()}</span>
            </div>
            <p class="text-light mb-2" style="font-size: 0.9rem;">${r.comment}</p>
            <div class="text-muted" style="font-size: 0.78rem;"><i class="bi bi-patch-check-fill text-success me-1"></i> ${r.user_name}</div>
        </div>
    `).join("");
}

async function submitReview(e) {
    e.preventDefault();
    if (!currentProduct) return;

    const rating = parseInt(document.getElementById("reviewRatingSelect").value);
    const title = document.getElementById("reviewTitleInput").value.trim();
    const comment = document.getElementById("reviewCommentInput").value.trim();

    if (!comment) {
        showToast("Please enter review comments.", "danger");
        return;
    }

    try {
        const res = await authFetch(`/products/${currentProduct.id}/reviews`, {
            method: "POST",
            body: JSON.stringify({ rating, title, comment })
        });

        if (res.ok) {
            showToast("Review submitted successfully! Thank you.", "success");
            // Dismiss modal
            const modalEl = document.getElementById("writeReviewModal");
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();

            // Refresh product details
            initProductDetailPage();
        } else {
            const data = await res.json();
            showToast(data.detail || "Failed to submit review.", "danger");
        }
    } catch (err) {
        showToast("Network error submitting review.", "danger");
    }
}

// -----------------------------------------------------------------------------
// Related Products
// -----------------------------------------------------------------------------
async function loadRelatedProducts(categoryId, excludeProductId) {
    const container = document.getElementById("relatedProductsGrid");
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/products?category=${categoryId}&limit=4`);
        const products = await res.json();
        const filtered = products.filter(p => p.id !== excludeProductId).slice(0, 4);

        if (filtered.length === 0) {
            container.parentElement.style.display = "none";
            return;
        }

        container.innerHTML = filtered.map(renderProductCardHTML).join("");
    } catch (e) {
        console.warn("Related products fetch failed", e);
    }
}

// DOM Init
document.addEventListener("DOMContentLoaded", () => {
    loadHomeProducts();
    initShopPage();
    initProductDetailPage();

    const reviewForm = document.getElementById("writeReviewForm");
    if (reviewForm) {
        reviewForm.addEventListener("submit", submitReview);
    }
});
