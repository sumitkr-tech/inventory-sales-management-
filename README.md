# ⚡ NovaStock - Inventory & Sales Management System
### 🎓 Academic Project-Based Learning (PBL) Submission

A full-stack, Object-Oriented retail inventory, Point of Sale (POS), and business intelligence web application built for small shops. The system manages product catalogs, updates stock automatically upon checkout, handles billing with sales tax and discounts, raises custom domain exceptions, persists records into CSV data files, and generates visual analytical graphs using **Pandas** and **Matplotlib**.

Hosted locally on: **`http://127.0.0.1:5000`** | Interactive Slide Deck: **`http://127.0.0.1:5000/presentation`**

---

## 🌟 Quick Start (1-Click Run)

### On Windows:
Double-click **`start_server.bat`** in the project folder. It will automatically detect Python, start the local server, and open your web browser.

### Via Command Line:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py
# (or if using Python 3.11: py -3.11 app.py)
```

The system will start on:
```
=================================================
>> Inventory & Sales Management System
>> Localhost URL: http://127.0.0.1:5000
>> Presentation:  http://127.0.0.1:5000/presentation
=================================================
```

---

## 🎯 PBL Requirements & Implementation Checklist

| Requirement | Description | Implementation Status |
|---|---|---|
| **Add Products** | Add new products with Product ID, Name, Category, Price, and Quantity | ✅ Fully implemented with validation |
| **Product Storage** | Stores: Product ID, Product Name, Category, Price, Quantity | ✅ Encapsulated in `Product` class |
| **Search Products** | Search across Product ID, Name, or Category | ✅ Real-time debounce search |
| **Update Stock** | Restock (+delta) or override quantity directly | ✅ Quick restock modal & API |
| **Record Sales** | Multi-item checkout with customer & payment method | ✅ Atomic 2-pass deduction |
| **Calculate Bill / Total** | Computes subtotal, tax (5%), discounts, and total | ✅ Line-item & grand total math |
| **Low-Stock Detection** | Detects products with quantity $\le 5$ units | ✅ Global alert banner & dedicated tab |
| **Sort Products** | Sort catalog by **Price**, **Quantity**, or **Sales** (asc/desc) | ✅ Implemented via Python lambdas |
| **File Persistence** | Store inventory and sales in files | ✅ `data/inventory.csv` & `data/sales.csv` |
| **Class: Product** | Class encapsulating product state and stock methods | ✅ `models/product.py` |
| **Class: Inventory** | Class managing catalog collection, search, and sales | ✅ `models/inventory.py` |
| **Class: Sale** | Class handling transaction billing and flat CSV rows | ✅ `models/sale.py` |
| **Pandas Analysis** | Aggregate revenue, AOV, order volume, category splits | ✅ `services/analytics.py` |
| **Matplotlib Graph 1** | **Product-wise sales graph** | ✅ Horizontal Bar Chart with revenue labels |
| **Matplotlib Graph 2** | **Category-wise sales graph** | ✅ Aesthetic Donut Chart with percentages |
| **Matplotlib Graph 3** | **Monthly sales graph** | ✅ Time-Series Area Chart with markers |
| **Custom Exceptions** | `InvalidProductIDError` & `InsufficientStockError` | ✅ `models/exceptions.py` with HTTP mapping |
| **Standout Innovations** | Slide deck, Web Audio, Dual Theme, CSV Export | ✅ Exceeds PBL expectations! |

---

## 💎 Innovations That Make This Project Stand Out

1. **🎯 Built-In Interactive Presentation Deck (`/presentation`)**:
   - A full 12-slide interactive presentation viewer styled like Apple Keynote / Reveal.js directly inside the web app.
   - Supports keyboard arrow navigation (`←`, `→`, `Space`), fullscreen mode (`F`), progress tracking bar, and presentation notes.
2. **🎵 Web Audio API Sound Feedback**:
   - Zero-dependency browser-synthesized audio effects (pleasant barcode beep on item add, multi-tone chime on checkout, and caution tone on error). Includes sound mute toggle.
3. **🌓 Dual Theme Support (Dark & Light Mode)**:
   - Modern dark glassmorphic mode and clean light theme with persistent storage in `localStorage`.
4. **📥 1-Click CSV Export Suite**:
   - Instant download buttons for active catalog (`/api/export/inventory`) and sales audit history (`/api/export/sales`).
5. **🧾 Printable Thermal & A4 Invoice Template**:
   - Clean printable invoice modal (`/receipt/<sale_id>`) formatted for standard 80mm POS receipt printers or PDF printing.
---

## 🏗️ System Architecture & Object-Oriented Design

```
Inventory-Sales-Management-System/
├── app.py                      # Flask backend, REST API & web routing
├── run.py                      # Smart launcher with environment auto-detect
├── start_server.bat            # 1-click Windows launcher
├── Procfile                    # Cloud hosting WSGI definition
├── render.yaml                 # 1-click deployment configuration for Render.com
├── requirements.txt            # Python package dependencies
├── README.md                   # Complete academic documentation
├── models/
│   ├── __init__.py             # Exports Product, Inventory, Sale, Exceptions
│   ├── product.py              # Product class (Encapsulation, validation, stock methods)
│   ├── inventory.py            # Inventory class (Catalog dictionary, search, sort, sales)
│   ├── sale.py                 # Sale & SaleItem classes (Billing math, flat row serialization)
│   └── exceptions.py           # Custom exception hierarchy
├── services/
│   ├── __init__.py
│   ├── analytics.py            # Pandas data aggregation & Matplotlib Agg chart generation
│   └── seeder.py               # Realistic multi-month sample data generator
├── data/
│   ├── inventory.csv           # Persistent inventory catalog
│   └── sales.csv               # Persistent sales transaction ledger
├── templates/
│   ├── index.html              # Main single-page application dashboard
│   ├── receipt.html            # Standalone printable thermal receipt
│   └── presentation.html       # In-browser full-screen interactive slide deck
├── static/
│   ├── css/
│   │   └── style.css           # Design system (Dark glassmorphic + Light theme)
│   └── js/
│       └── app.js              # Client state, POS cart, Web Audio, API caller
└── tests/
    ├── __init__.py
    ├── test_system.py          # Unit tests for OOP classes, methods, and exceptions
    └── test_e2e.py             # End-to-end integration tests (12 endpoints verified)
```

---

## 🧩 Core Classes Detailed Explanation

### 1. `Product` ([`models/product.py`](file:///c:/Users/SHRUTI%20PAL/Downloads/Inventory-Sales-Management-System/models/product.py))
Encapsulates individual merchandise items:
- **Attributes**: `product_id`, `name`, `category`, `price`, `quantity`.
- **Validation**:
  - `validate()`: Ensures non-empty ID and name, non-negative price (`price >= 0`), non-negative quantity (`quantity >= 0`).
- **Methods**:
  - `update_stock(quantity_delta)`: Safely increments or decrements quantity.
  - `set_quantity(quantity)`: Direct quantity adjustment.
  - `is_low_stock(threshold=5)`: Evaluates if stock is at or below threshold.
  - `total_stock_value`: Property computing `price * quantity`.
  - `to_dict()` / `from_dict()`: Serialization helpers.

### 2. `Inventory` ([`models/inventory.py`](file:///c:/Users/SHRUTI%20PAL/Downloads/Inventory-Sales-Management-System/models/inventory.py))
Manages catalog collection and file persistence:
- **Attributes**: `products: Dict[str, Product]`, `inventory_file`, `sales_file`.
- **File Persistence**:
  - `_load_inventory()`: Reads `data/inventory.csv` into memory on startup.
  - `save_to_file()`: Writes the current in-memory catalog back to `data/inventory.csv`.
- **Search & Sort**:
  - `search_products(query)`: Case-insensitive match on ID, Name, or Category.
  - `sort_products(sort_by, ascending)`: Sorts by `price`, `quantity`, or `sales`.
  - `get_product_sales_counts()`: Aggregates total units sold per product from `sales.csv` for sorting by sales.
- **Atomic Sales Execution**:
  - `record_sale(items_data, customer_name, payment_method, tax_rate)`:
    - **Pass 1**: Verifies all products exist and have sufficient stock. Raises `InvalidProductIDError` or `InsufficientStockError` if any item fails.
    - **Pass 2**: Deducts stock only after all items have been verified.
    - **Pass 3**: Saves inventory and appends transactions to `data/sales.csv`.

### 3. `Sale` & `SaleItem` ([`models/sale.py`](file:///c:/Users/SHRUTI%20PAL/Downloads/Inventory-Sales-Management-System/models/sale.py))
Encapsulates transaction invoices and billing:
- **`SaleItem`**: Represents a single line item (`unit_price * quantity = subtotal`).
- **`Sale`**:
  - Computes `subtotal`, `tax_amount` (5%), and `total_amount`.
  - Generates unique sequential `sale_id` (e.g. `INV-1001`).
  - `to_flat_rows()`: Converts order structure into tabular records for CSV appending.

### 4. Custom Exceptions ([`models/exceptions.py`](file:///c:/Users/SHRUTI%20PAL/Downloads/Inventory-Sales-Management-System/models/exceptions.py))
- `InventorySalesException` (Base class, inherits `Exception`, maps to HTTP code and JSON payload)
  - `InvalidProductIDError` (HTTP 404: raised when querying/selling a product ID not in inventory)
  - `InsufficientStockError` (HTTP 400: raised when requested quantity > available stock)
  - `DuplicateProductIDError` (HTTP 409: raised when adding a duplicate product ID)
  - `InvalidProductDataError` (HTTP 400: raised on negative values or empty fields)

---

## 📊 Sales Analytics with Pandas & Matplotlib

Located in [`services/analytics.py`](file:///c:/Users/SHRUTI%20PAL/Downloads/Inventory-Sales-Management-System/services/analytics.py):

### 1. Pandas Aggregation
- Ingests `data/sales.csv` into a typed DataFrame with datetime index (`year_month`, `date`).
- Calculates:
  - **Total Revenue**: Sum of `total_amount`.
  - **Average Order Value (AOV)**: Revenue divided by unique `sale_id` count.
  - **Top Product**: Groupby `product_name` aggregated by revenue.
  - **Category Breakdown**: Groupby `category` aggregated by revenue and units.
  - **Monthly Aggregations**: Groupby `year_month` tracking revenue trends.

### 2. Matplotlib Graphs (Headless Web Server Mode)
- Configured with `matplotlib.use("Agg")` for thread-safe in-memory rendering.
- Converts plots directly to Base64 encoded PNG data streams:
  1. **Product-Wise Sales Graph**: Horizontal bar chart of top items with value labels ($).
  2. **Category-Wise Sales Graph**: Donut chart displaying category revenue contribution percentages.
  3. **Monthly Sales Graph**: Time-series area chart showing month-over-month revenue trends.

---

## 🧪 Automated Testing Suite

### 1. Unit Tests (Classes, Logic & Exceptions)
```bash
python -m unittest tests/test_system.py
```
**Output**:
```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.521s

OK
```
*Validates product validation, duplicate IDs, InsufficientStockError, InvalidProductIDError, sorting algorithms, and chart generation.*

### 2. End-to-End API & Integration Tests
```bash
python tests/test_e2e.py
```
**Output**:
```
>> Live server not running; using in-memory Flask Test Client...

1. Testing GET /api/metrics ... [SUCCESS]
2. Testing GET /api/inventory?sort_by=price&order=desc ... [SUCCESS]
3. Testing GET /api/analytics (Pandas & Matplotlib) ... [SUCCESS]
4. Testing POST /api/sales (Valid Transaction) ... [SUCCESS]
5. Testing POST /api/sales with InsufficientStockError ... [SUCCESS]
6. Testing POST /api/sales with InvalidProductIDError ... [SUCCESS]
7. Testing GET /receipt/<sale_id> ... [SUCCESS]
8. Testing GET /presentation (Interactive Slide Deck) ... [SUCCESS]
9. Testing GET /api/export/inventory (CSV Export) ... [SUCCESS]
10. Testing GET /api/export/sales (CSV Export) ... [SUCCESS]
11. Testing GET /api/system-info ... [SUCCESS]

=======================================================
>> ALL 11 END-TO-END INTEGRATION TESTS PASSED 100%! <<
=======================================================
```

---

## 🌐 REST API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web application single-page dashboard |
| `GET` | `/presentation` | Full-screen interactive PBL presentation slide deck |
| `GET` | `/receipt/<id>` | Standalone printable thermal receipt invoice |
| `GET` | `/api/metrics` | Key performance indicators (valuation, revenue, stock) |
| `GET` | `/api/inventory` | Catalog list with search, filter, and sorting |
| `POST` | `/api/inventory` | Adds a new product with validation |
| `PUT` | `/api/inventory/<id>` | Updates product name, category, price, or quantity |
| `POST` | `/api/inventory/<id>/stock`| Quick restock or quantity override |
| `DELETE`| `/api/inventory/<id>` | Deletes product from catalog |
| `POST` | `/api/sales` | Records sale atomically and deducts stock |
| `GET` | `/api/sales` | Returns past sales invoices |
| `GET` | `/api/analytics` | Pandas statistics and 3 Matplotlib Base64 charts |
| `GET` | `/api/export/inventory` | Downloads `inventory_catalog_export.csv` |
| `GET` | `/api/export/sales` | Downloads `sales_history_export.csv` |
| `GET` | `/api/system-info` | Runtime environment & OOP metadata |
| `POST` | `/api/reset-demo` | Seeds multi-month realistic demonstration data |

---

## ☁️ Cloud Hosting & Deployment Guide

The project is pre-configured for free cloud hosting platforms:

### Option A: Render.com (Recommended)
1. Push the code to a GitHub repository.
2. Sign in to [Render.com](https://render.com) and click **New Web Service**.
3. Connect your repository.
4. Render will automatically detect `render.yaml`:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
5. Click **Create Web Service** — your app is live on a public HTTPS URL!

### Option B: Railway.app / Heroku
The included `Procfile` (`web: gunicorn --bind 0.0.0.0:$PORT app:app`) supports deployment on Railway or Heroku.

### Option C: PythonAnywhere
1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com).
2. Upload the project folder.
3. In the Web tab, point the WSGI configuration to `app.py`.

---

## 🎓 PBL Viva / Oral Examination Questions & Answers

### Q1: What are the main classes in your project and their responsibilities?
> **Answer**: The system uses three primary classes:
> 1. `Product`: Encapsulates item attributes (`product_id`, `name`, `category`, `price`, `quantity`), validates positive values, and manages stock changes.
> 2. `Inventory`: Manages the catalog collection in a dictionary, coordinates CSV persistence, handles case-insensitive search, multi-criteria sorting, and atomic sales execution.
> 3. `Sale` & `SaleItem`: Encapsulate transactions, compute line totals, 5% sales tax, and grand totals, and convert orders to flat rows for CSV storage.
> In addition, `SalesAnalytics` encapsulates data science aggregations using Pandas and Matplotlib.

### Q2: Why are custom exceptions used instead of standard Python exceptions?
> **Answer**: Standard exceptions like `ValueError` or `KeyError` don't convey domain meaning and can't easily carry structured metadata. Our custom exceptions (`InvalidProductIDError`, `InsufficientStockError`) carry specific business details (the requested quantity vs available stock, the specific missing product ID) and map directly to appropriate HTTP status codes (404 Not Found, 400 Bad Request) for clean API responses.

### Q3: How is atomic stock deduction ensured when selling multiple items?
> **Answer**: We use a two-pass algorithm in `Inventory.record_sale()`:
> - **Pass 1 (Verification)**: Checks all items to ensure every product exists and has sufficient stock. If any item fails, an exception is thrown immediately.
> - **Pass 2 (Deduction)**: Only executes if all items pass verification. Then and only then are stocks decremented and written to the CSV file. This prevents partial sales and negative inventory.

### Q4: Why use Matplotlib with the 'Agg' backend?
> **Answer**: By default, Matplotlib tries to launch a graphical window (Tkinter or Qt), which is impossible or hazardous in a web server environment and will block threads or crash. `matplotlib.use("Agg")` runs headless, drawing figures directly to an in-memory byte buffer that is encoded as a Base64 PNG image string and sent to the browser.

### Q5: How is file persistence handled without an external database?
> **Answer**: Inventory is stored in `data/inventory.csv` with columns `product_id,name,category,price,quantity`. Sales are stored in `data/sales.csv` as an append-only audit ledger. Python's built-in `csv.DictReader` and `csv.DictWriter` handle serialisation with headers, making the dataset inspectable in Excel or Google Sheets with zero database installation required.

---

## 👥 Contributors & Academic Acknowledgements
Developed as part of the **Project-Based Learning (PBL)** Curriculum for Computer Science & Information Technology.
All code adheres to clean Python PEP 8 standards, strict Object-Oriented Principles, and modern web application development best practices.
