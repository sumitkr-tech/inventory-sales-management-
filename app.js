/**
 * Frontend Application Logic for Inventory & Sales Management System
 * Handles UI interactions, POS cart, REST APIs, modals, and dynamic rendering.
 */

// Global State
let allProducts = [];
let cart = {}; // product_id -> { product, quantity }
let searchDebounceTimeout = null;

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSound();
    initTabs();
    loadDashboard();
    loadCategories();
    loadInventoryTable();
    loadPOSProducts();
});

// ---------------- Navigation & Tabs ----------------

function initTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(el => {
        el.classList.toggle("active", el.getAttribute("data-tab") === tabId);
    });

    document.querySelectorAll(".tab-content").forEach(el => {
        el.classList.toggle("active", el.id === tabId);
    });

    // Refresh specific tab data on switch
    if (tabId === "tab-dashboard") loadDashboard();
    if (tabId === "tab-inventory") loadInventoryTable();
    if (tabId === "tab-pos") loadPOSProducts();
    if (tabId === "tab-lowstock") loadLowStockTab();
    if (tabId === "tab-sales") loadSalesHistory();
    if (tabId === "tab-analytics") loadAnalyticsData();
}

// ---------------- Dashboard & KPIs ----------------

async function loadDashboard() {
    try {
        const res = await fetch("/api/metrics");
        const data = await res.json();

        document.getElementById("kpi-inventory-val").textContent = `$${data.total_inventory_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById("kpi-stock-units").textContent = `${data.total_stock_units} total units across catalog`;
        document.getElementById("kpi-total-revenue").textContent = `$${data.total_revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById("kpi-total-orders").textContent = `${data.total_orders} completed orders (${data.total_items_sold} items sold)`;
        document.getElementById("kpi-product-count").textContent = data.total_products;
        document.getElementById("kpi-lowstock-count").textContent = data.low_stock_count;

        // Nav pill badge
        const badge = document.getElementById("nav-lowstock-badge");
        if (badge) badge.textContent = data.low_stock_count;

        // Banner
        const banner = document.getElementById("low-stock-banner");
        if (data.low_stock_count > 0) {
            banner.style.display = "flex";
            document.getElementById("low-stock-banner-text").textContent =
                `Attention: ${data.low_stock_count} item(s) have 5 or fewer units remaining in stock.`;
        } else {
            banner.style.display = "none";
        }

        loadRecentSales();
        loadLowStockWatchlist();
    } catch (err) {
        console.error("Failed loading dashboard metrics:", err);
    }
}

async function loadRecentSales() {
    try {
        const res = await fetch("/api/sales?limit=6");
        const sales = await res.json();
        const tbody = document.querySelector("#dashboard-recent-sales tbody");
        tbody.innerHTML = "";

        if (!sales || sales.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No sales records found.</td></tr>`;
            return;
        }

        sales.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="mono-cell" style="font-weight: 600; color: #38bdf8;">${s.sale_id}</td>
                <td style="font-size: 0.8rem; color: var(--text-muted);">${s.timestamp}</td>
                <td>${escapeHtml(s.customer_name)}</td>
                <td class="mono-cell">${s.total_units}</td>
                <td class="mono-cell" style="font-weight: 700; color: #34d399;">$${s.total_amount.toFixed(2)}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openReceiptModal('${s.sale_id}')">Receipt</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed loading recent sales:", err);
    }
}

async function loadLowStockWatchlist() {
    try {
        const res = await fetch("/api/inventory?low_stock=true&threshold=5");
        const items = await res.json();
        const container = document.getElementById("dashboard-low-list");
        const countBadge = document.getElementById("dashboard-low-badge");
        container.innerHTML = "";
        countBadge.textContent = `${items.length} items`;

        if (items.length === 0) {
            container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px; font-size: 0.85rem;">All products are adequately stocked! 🎉</div>`;
            return;
        }

        items.forEach(p => {
            const card = document.createElement("div");
            card.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; margin-bottom: 8px; background: var(--bg-surface); border-radius: var(--radius-sm); border: 1px solid var(--border-color);";
            card.innerHTML = `
                <div>
                    <div style="font-weight: 600; font-size: 0.88rem;">${escapeHtml(p.name)}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${p.product_id} &bull; ${escapeHtml(p.category)}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="badge badge-danger">${p.quantity} left</span>
                    <button class="btn btn-emerald btn-sm" onclick="openRestockModal('${p.product_id}', '${escapeHtml(p.name)}', ${p.quantity})">+ Restock</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed loading low stock watchlist:", err);
    }
}

// ---------------- Categories Loader ----------------

async function loadCategories() {
    try {
        const res = await fetch("/api/categories");
        const categories = await res.json();

        // Populate filter dropdowns
        const invSelect = document.getElementById("inventory-cat-filter");
        const posSelect = document.getElementById("pos-cat-filter");
        const datalist = document.getElementById("category-datalist");

        invSelect.innerHTML = '<option value="">All Categories</option>';
        posSelect.innerHTML = '<option value="">All Categories</option>';
        datalist.innerHTML = '';

        categories.forEach(c => {
            invSelect.innerHTML += `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`;
            posSelect.innerHTML += `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`;
            datalist.innerHTML += `<option value="${escapeHtml(c)}">`;
        });
    } catch (err) {
        console.error("Failed loading categories:", err);
    }
}

// ---------------- Inventory Tab (Search, Sort, CRUD) ----------------

function debounceInventorySearch() {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
        loadInventoryTable();
    }, 250);
}

async function loadInventoryTable() {
    const search = document.getElementById("inventory-search").value;
    const category = document.getElementById("inventory-cat-filter").value;
    const sortBy = document.getElementById("inventory-sort-by").value;
    const order = document.getElementById("inventory-sort-order").value;

    const queryParams = new URLSearchParams({
        search: search,
        category: category,
        sort_by: sortBy,
        order: order
    });

    try {
        const res = await fetch(`/api/inventory?${queryParams.toString()}`);
        const products = await res.json();
        allProducts = products;

        const tbody = document.querySelector("#inventory-table tbody");
        tbody.innerHTML = "";

        if (products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 30px;">No matching products found.</td></tr>`;
            return;
        }

        products.forEach(p => {
            const tr = document.createElement("tr");
            if (p.is_low_stock) {
                tr.classList.add("low-stock-row");
            }

            const stockBadge = p.quantity <= 0
                ? `<span class="badge badge-danger">Out of Stock (0)</span>`
                : p.is_low_stock
                ? `<span class="badge badge-warning">Low: ${p.quantity} units</span>`
                : `<span class="badge badge-success">${p.quantity} units</span>`;

            tr.innerHTML = `
                <td class="mono-cell" style="font-weight: 600; color: #38bdf8;">${p.product_id}</td>
                <td>
                    <div style="font-weight: 600;">${escapeHtml(p.name)}</div>
                </td>
                <td>
                    <span class="badge badge-category">${escapeHtml(p.category)}</span>
                </td>
                <td class="mono-cell" style="font-weight: 600;">$${p.price.toFixed(2)}</td>
                <td>${stockBadge}</td>
                <td class="mono-cell" style="color: var(--text-secondary);">$${p.stock_value.toFixed(2)}</td>
                <td class="mono-cell" style="font-weight: 600; color: #a5b4fc;">${p.units_sold || 0}</td>
                <td style="text-align: right;">
                    <div style="display: inline-flex; gap: 6px;">
                        <button class="btn btn-emerald btn-sm" title="Quick Restock" onclick="openRestockModal('${p.product_id}', '${escapeHtml(p.name)}', ${p.quantity})">Restock</button>
                        <button class="btn btn-secondary btn-sm" title="Edit" onclick="openEditModal('${p.product_id}')">Edit</button>
                        <button class="btn btn-danger btn-sm" title="Delete" onclick="deleteProduct('${p.product_id}', '${escapeHtml(p.name)}')">Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed loading inventory:", err);
    }
}

// ---------------- Product Modals & Handlers ----------------

function openAddProductModal() {
    document.getElementById("form-add-product").reset();
    document.getElementById("modal-add-product").classList.add("open");
}

async function handleAddProduct(event) {
    event.preventDefault();
    const pid = document.getElementById("add-product-id").value.trim();
    const name = document.getElementById("add-product-name").value.trim();
    const category = document.getElementById("add-product-category").value.trim();
    const price = parseFloat(document.getElementById("add-product-price").value);
    const quantity = parseInt(document.getElementById("add-product-quantity").value);

    try {
        const res = await fetch("/api/inventory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: pid, name, category, price, quantity })
        });
        const data = await res.json();

        if (!res.ok) {
            handleExceptionResponse(data);
            return;
        }

        showToast(data.message, "success");
        closeModal("modal-add-product");
        loadInventoryTable();
        loadCategories();
        loadDashboard();
        loadPOSProducts();
    } catch (err) {
        showToast("Error adding product", "error");
    }
}

async function openEditModal(productId) {
    try {
        const res = await fetch(`/api/inventory/${productId}`);
        const p = await res.json();

        if (!res.ok) {
            handleExceptionResponse(p);
            return;
        }

        document.getElementById("edit-product-id").value = p.product_id;
        document.getElementById("edit-product-id-display").value = p.product_id;
        document.getElementById("edit-product-name").value = p.name;
        document.getElementById("edit-product-category").value = p.category;
        document.getElementById("edit-product-price").value = p.price;
        document.getElementById("edit-product-quantity").value = p.quantity;

        document.getElementById("modal-edit-product").classList.add("open");
    } catch (err) {
        showToast("Error fetching product details", "error");
    }
}

async function handleEditProduct(event) {
    event.preventDefault();
    const pid = document.getElementById("edit-product-id").value;
    const name = document.getElementById("edit-product-name").value.trim();
    const category = document.getElementById("edit-product-category").value.trim();
    const price = parseFloat(document.getElementById("edit-product-price").value);
    const quantity = parseInt(document.getElementById("edit-product-quantity").value);

    try {
        const res = await fetch(`/api/inventory/${pid}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, category, price, quantity })
        });
        const data = await res.json();

        if (!res.ok) {
            handleExceptionResponse(data);
            return;
        }

        showToast(data.message, "success");
        closeModal("modal-edit-product");
        loadInventoryTable();
        loadCategories();
        loadDashboard();
        loadPOSProducts();
    } catch (err) {
        showToast("Error updating product", "error");
    }
}

function openRestockModal(productId, productName, currentQty) {
    document.getElementById("restock-product-id").value = productId;
    document.getElementById("restock-product-name").textContent = productName;
    document.getElementById("restock-current-qty").textContent = currentQty;
    document.getElementById("restock-add-qty").value = 10;
    document.getElementById("modal-restock").classList.add("open");
}

async function handleQuickRestock(event) {
    event.preventDefault();
    const pid = document.getElementById("restock-product-id").value;
    const qty = parseInt(document.getElementById("restock-add-qty").value);

    try {
        const res = await fetch(`/api/inventory/${pid}/stock`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity: qty, mode: "add" })
        });
        const data = await res.json();

        if (!res.ok) {
            handleExceptionResponse(data);
            return;
        }

        showToast(data.message, "success");
        closeModal("modal-restock");
        loadInventoryTable();
        loadDashboard();
        loadLowStockTab();
        loadPOSProducts();
    } catch (err) {
        showToast("Error updating stock", "error");
    }
}

async function deleteProduct(productId, productName) {
    if (!confirm(`Are you sure you want to delete product '${productName}' (ID: ${productId}) from inventory?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/inventory/${productId}`, { method: "DELETE" });
        const data = await res.json();

        if (!res.ok) {
            handleExceptionResponse(data);
            return;
        }

        showToast(data.message, "success");
        loadInventoryTable();
        loadCategories();
        loadDashboard();
        loadPOSProducts();
    } catch (err) {
        showToast("Failed to delete product", "error");
    }
}

// ---------------- POS & Billing System ----------------

async function loadPOSProducts() {
    try {
        const res = await fetch("/api/inventory?sort_by=name&order=asc");
        const products = await res.json();
        renderPOSProducts(products);
    } catch (err) {
        console.error("Failed loading POS products:", err);
    }
}

function filterPOSProducts() {
    const query = document.getElementById("pos-search").value.toLowerCase();
    const cat = document.getElementById("pos-cat-filter").value.toLowerCase();

    const filtered = allProducts.filter(p => {
        const matchQ = p.name.toLowerCase().includes(query) || p.product_id.toLowerCase().includes(query);
        const matchC = !cat || p.category.toLowerCase() === cat;
        return matchQ && matchC;
    });
    renderPOSProducts(filtered);
}

function renderPOSProducts(products) {
    const grid = document.getElementById("pos-products-list");
    grid.innerHTML = "";

    if (products.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 30px;">No products found in catalog.</div>`;
        return;
    }

    products.forEach(p => {
        const card = document.createElement("div");
        card.className = `pos-product-card ${p.quantity <= 0 ? 'out-of-stock' : ''}`;
        card.onclick = () => {
            if (p.quantity > 0) {
                addToCart(p);
            } else {
                showToast(`'${p.name}' is out of stock!`, "warning");
            }
        };

        card.innerHTML = `
            <div>
                <div class="pos-card-header">
                    <span class="badge badge-category" style="font-size: 0.7rem;">${escapeHtml(p.category)}</span>
                    <span class="pos-card-stock ${p.is_low_stock ? 'badge badge-warning' : ''}" style="font-size: 0.72rem;">
                        ${p.quantity} in stock
                    </span>
                </div>
                <div class="pos-card-title">${escapeHtml(p.name)}</div>
                <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${p.product_id}</div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 10px;">
                <div class="pos-card-price">$${p.price.toFixed(2)}</div>
                <button class="btn btn-secondary btn-sm" style="padding: 4px 8px;">+ Add</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function addToCart(product) {
    hidePOSError();
    if (!cart[product.product_id]) {
        cart[product.product_id] = {
            product: product,
            quantity: 1
        };
    } else {
        // Check local stock limit
        if (cart[product.product_id].quantity + 1 > product.quantity) {
            showToast(`Cannot add more than available stock (${product.quantity})!`, "warning");
            playAudioBeep("error");
            return;
        }
        cart[product.product_id].quantity += 1;
    }
    playAudioBeep("add");
    renderCart();
}

function updateCartQty(productId, delta) {
    hidePOSError();
    if (!cart[productId]) return;

    const newQty = cart[productId].quantity + delta;
    if (newQty <= 0) {
        delete cart[productId];
    } else {
        if (newQty > cart[productId].product.quantity) {
            showToast(`Requested quantity exceeds available stock (${cart[productId].product.quantity})!`, "warning");
            return;
        }
        cart[productId].quantity = newQty;
    }
    renderCart();
}

function clearCart() {
    cart = {};
    hidePOSError();
    renderCart();
}

function renderCart() {
    const container = document.getElementById("pos-cart-items");
    const countSpan = document.getElementById("cart-item-count");
    const subtotalEl = document.getElementById("pos-subtotal");
    const taxEl = document.getElementById("pos-tax");
    const totalEl = document.getElementById("pos-total");

    const items = Object.values(cart);
    countSpan.textContent = items.reduce((sum, i) => sum + i.quantity, 0);

    if (items.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 30px 10px; font-size: 0.85rem;">
                No items in bill yet.<br>Click any product on the left to add.
            </div>
        `;
        subtotalEl.textContent = "$0.00";
        taxEl.textContent = "$0.00";
        totalEl.textContent = "$0.00";
        return;
    }

    container.innerHTML = "";
    let subtotal = 0;

    items.forEach(item => {
        const p = item.product;
        const lineTotal = p.price * item.quantity;
        subtotal += lineTotal;

        const row = document.createElement("div");
        row.className = "cart-item-row";
        row.innerHTML = `
            <div class="cart-item-info">
                <div style="font-weight: 600;">${escapeHtml(p.name)}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">$${p.price.toFixed(2)} each</div>
            </div>
            <div class="cart-item-controls">
                <button class="qty-btn" onclick="updateCartQty('${p.product_id}', -1)">&minus;</button>
                <span class="mono-cell" style="font-weight: 700; min-width: 20px; text-align: center;">${item.quantity}</span>
                <button class="qty-btn" onclick="updateCartQty('${p.product_id}', 1)">&plus;</button>
            </div>
            <div class="mono-cell" style="font-weight: 700; width: 65px; text-align: right;">$${lineTotal.toFixed(2)}</div>
        `;
        container.appendChild(row);
    });

    // Discount Calculation
    const discountSelect = document.getElementById("pos-discount");
    const discountPct = discountSelect ? parseFloat(discountSelect.value) || 0 : 0;
    const discountAmt = roundToTwo((subtotal * discountPct) / 100);
    const discountedSubtotal = Math.max(0, subtotal - discountAmt);

    const discountLine = document.getElementById("pos-discount-line");
    const discountAmtEl = document.getElementById("pos-discount-amt");
    if (discountLine && discountAmtEl) {
        if (discountPct > 0) {
            discountLine.style.display = "flex";
            discountAmtEl.textContent = `-$${discountAmt.toFixed(2)} (${discountPct}%)`;
        } else {
            discountLine.style.display = "none";
        }
    }

    const tax = roundToTwo(discountedSubtotal * 0.05);
    const grandTotal = roundToTwo(discountedSubtotal + tax);

    subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    taxEl.textContent = `$${tax.toFixed(2)}`;
    totalEl.textContent = `$${grandTotal.toFixed(2)}`;
}

async function submitSaleOrder() {
    const items = Object.values(cart).map(i => ({
        product_id: i.product.product_id,
        quantity: i.quantity
    }));

    if (items.length === 0) {
        showToast("Cart is empty! Please add products to bill.", "warning");
        return;
    }

    const customerName = document.getElementById("pos-customer").value.trim() || "Walk-in Customer";
    const paymentMethod = document.getElementById("pos-payment").value;

    try {
        const res = await fetch("/api/sales", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_name: customerName,
                payment_method: paymentMethod,
                tax_rate: 0.05,
                items: items
            })
        });

        const data = await res.json();

        if (!res.ok) {
            // Domain Exception handled! E.g. InsufficientStockError or InvalidProductIDError
            playAudioBeep("error");
            handleExceptionResponse(data);
            showPOSError(data.error, data.message);
            return;
        }

        playAudioBeep("success");
        showToast("Sale completed successfully! 🎉", "success");
        clearCart();
        loadDashboard();
        loadInventoryTable();
        loadPOSProducts();

        // Automatically open the invoice modal
        if (data.sale && data.sale.sale_id) {
            openReceiptModal(data.sale.sale_id);
        }
    } catch (err) {
        showToast("Transaction failed. Check server logs.", "error");
    }
}

function showPOSError(title, msg) {
    const box = document.getElementById("pos-exception-box");
    document.getElementById("pos-exception-title").textContent = title || "Stock Error";
    document.getElementById("pos-exception-msg").textContent = msg;
    box.classList.add("show");
}

function hidePOSError() {
    document.getElementById("pos-exception-box").classList.remove("show");
}

// ---------------- Low Stock Tab ----------------

async function loadLowStockTab() {
    const thresholdInput = document.getElementById("low-stock-threshold-input");
    const threshold = parseInt(thresholdInput.value) || 5;

    try {
        const res = await fetch(`/api/inventory?low_stock=true&threshold=${threshold}`);
        const products = await res.json();
        const tbody = document.querySelector("#lowstock-table tbody");
        tbody.innerHTML = "";

        if (products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #34d399; padding: 30px;">✅ Great! No products currently have stock below ${threshold} units.</td></tr>`;
            return;
        }

        products.forEach(p => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="mono-cell" style="font-weight: 600; color: #38bdf8;">${p.product_id}</td>
                <td><div style="font-weight: 600;">${escapeHtml(p.name)}</div></td>
                <td><span class="badge badge-category">${escapeHtml(p.category)}</span></td>
                <td>
                    <span class="badge ${p.quantity === 0 ? 'badge-danger' : 'badge-warning'} mono-cell" style="font-size: 0.85rem;">
                        ${p.quantity} units
                    </span>
                </td>
                <td class="mono-cell">$${p.price.toFixed(2)}</td>
                <td>
                    <span style="color: #fb7185; font-size: 0.8rem; font-weight: 600;">
                        ${p.quantity === 0 ? '🚨 OUT OF STOCK' : '⚠️ LOW STOCK'}
                    </span>
                </td>
                <td style="text-align: right;">
                    <button class="btn btn-emerald btn-sm" onclick="openRestockModal('${p.product_id}', '${escapeHtml(p.name)}', ${p.quantity})">
                        + Restock
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed loading low stock products:", err);
    }
}

// ---------------- Sales History Tab ----------------

async function loadSalesHistory() {
    try {
        const res = await fetch("/api/sales?limit=100");
        const sales = await res.json();
        const tbody = document.querySelector("#sales-history-table tbody");
        tbody.innerHTML = "";

        if (sales.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 30px;">No sales records found in sales.csv.</td></tr>`;
            return;
        }

        sales.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="mono-cell" style="font-weight: 600; color: #38bdf8;">${s.sale_id}</td>
                <td style="font-size: 0.82rem; color: var(--text-muted);">${s.timestamp}</td>
                <td>${escapeHtml(s.customer_name)}</td>
                <td><span class="badge badge-category">${escapeHtml(s.payment_method)}</span></td>
                <td class="mono-cell">${s.total_units}</td>
                <td class="mono-cell">$${s.subtotal.toFixed(2)}</td>
                <td class="mono-cell">$${s.tax_amount.toFixed(2)}</td>
                <td class="mono-cell" style="font-weight: 700; color: #34d399;">$${s.total_amount.toFixed(2)}</td>
                <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="openReceiptModal('${s.sale_id}')">View Receipt</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed loading sales history:", err);
    }
}

// ---------------- Analytics Tab (Pandas & Matplotlib) ----------------

async function loadAnalyticsData() {
    try {
        const prodContainer = document.getElementById("chart-product-container");
        const catContainer = document.getElementById("chart-category-container");
        const monthContainer = document.getElementById("chart-monthly-container");

        prodContainer.innerHTML = '<span style="color: var(--text-muted);">Generating Matplotlib chart...</span>';
        catContainer.innerHTML = '<span style="color: var(--text-muted);">Generating Matplotlib chart...</span>';
        monthContainer.innerHTML = '<span style="color: var(--text-muted);">Generating Matplotlib chart...</span>';

        const res = await fetch("/api/analytics");
        const data = await res.json();

        // Update Pandas stats
        document.getElementById("pandas-aov").textContent = `$${data.summary.average_order_value.toFixed(2)}`;
        document.getElementById("pandas-top-product").textContent = data.summary.top_product || "N/A";
        document.getElementById("pandas-top-category").textContent = data.summary.top_category || "N/A";

        // Inject Matplotlib images
        if (data.charts.product_chart) {
            prodContainer.innerHTML = `<img src="${data.charts.product_chart}" alt="Product-wise Sales Graph">`;
        }
        if (data.charts.category_chart) {
            catContainer.innerHTML = `<img src="${data.charts.category_chart}" alt="Category-wise Sales Graph">`;
        }
        if (data.charts.monthly_chart) {
            monthContainer.innerHTML = `<img src="${data.charts.monthly_chart}" alt="Monthly Sales Graph">`;
        }
    } catch (err) {
        console.error("Failed loading analytics:", err);
        showToast("Error loading analytics charts", "error");
    }
}

async function resetDemoData() {
    if (!confirm("Reset and seed sample inventory and sales records?")) return;
    try {
        const res = await fetch("/api/reset-demo", { method: "POST" });
        const data = await res.json();
        showToast(data.message, "success");
        loadDashboard();
        loadInventoryTable();
        loadAnalyticsData();
    } catch (err) {
        showToast("Failed to reset sample data", "error");
    }
}

// ---------------- Receipt Modal ----------------

async function openReceiptModal(saleId) {
    try {
        const res = await fetch(`/receipt/${saleId}`);
        const html = await res.text();
        const container = document.getElementById("receipt-modal-content");
        container.innerHTML = html;
        document.getElementById("modal-receipt").classList.add("open");
    } catch (err) {
        showToast("Failed to fetch receipt", "error");
    }
}

// ---------------- Exception & Error Handling Modal ----------------

function handleExceptionResponse(errorObj) {
    const modal = document.getElementById("modal-exception");
    document.getElementById("exception-modal-name").textContent = errorObj.error || "System Error";
    document.getElementById("exception-modal-message").textContent = errorObj.message || "An unexpected error occurred.";
    document.getElementById("exception-modal-details").textContent = JSON.stringify(errorObj, null, 2);
    modal.classList.add("open");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("open");
}

// ---------------- CSV Export Handlers ----------------

function exportInventoryCSV() {
    window.location.href = "/api/export/inventory";
    showToast("Downloading inventory CSV...", "success");
}

function exportSalesCSV() {
    window.location.href = "/api/export/sales";
    showToast("Downloading sales history CSV...", "success");
}

// ---------------- Theme Management ----------------
let currentTheme = localStorage.getItem("novastock_theme") || "dark";

function initTheme() {
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeButton();
}

function toggleTheme() {
    currentTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", currentTheme);
    localStorage.setItem("novastock_theme", currentTheme);
    updateThemeButton();
}

function updateThemeButton() {
    const btn = document.getElementById("btn-theme-toggle");
    if (btn) {
        btn.textContent = currentTheme === "dark" ? "🌙" : "☀️";
        btn.title = currentTheme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode";
    }
}

// ---------------- Audio Sound FX (Web Audio API) ----------------
let soundEnabled = localStorage.getItem("novastock_sound") !== "false";

function initSound() {
    updateSoundButton();
}

function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem("novastock_sound", soundEnabled ? "true" : "false");
    updateSoundButton();
    if (soundEnabled) playAudioBeep("add");
}

function updateSoundButton() {
    const btn = document.getElementById("btn-sound-toggle");
    if (btn) {
        btn.textContent = soundEnabled ? "🔊" : "🔇";
        btn.title = soundEnabled ? "Audio Effects Enabled (Click to Mute)" : "Audio Effects Muted (Click to Enable)";
    }
}

function playAudioBeep(type = "add") {
    if (!soundEnabled) return;
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;
        if (type === "add") {
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.08); // A5
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
            osc.start(now);
            osc.stop(now + 0.1);
        } else if (type === "success") {
            // Chime: C5 -> G5
            osc.frequency.setValueAtTime(523.25, now);
            osc.frequency.setValueAtTime(659.25, now + 0.08);
            osc.frequency.setValueAtTime(783.99, now + 0.16);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc.start(now);
            osc.stop(now + 0.35);
        } else if (type === "error") {
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.linearRampToValueAtTime(160, now + 0.2);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc.start(now);
            osc.stop(now + 0.25);
        }
    } catch (e) {
        // Audio policy or unsupported
    }
}

// ---------------- Utilities ----------------

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideToast 0.3s ease reverse forwards";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function roundToTwo(num) {
    return Math.round((num + Number.EPSILON) * 100) / 100;
}
