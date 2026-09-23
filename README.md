# 🌿 Greeni5 - Modern Plant Nursery E-Commerce Platform

**Greeni5** is a complete, full-stack, nature-inspired e-commerce platform designed for online plant nurseries and botanical gardens. Customers can browse botanical varieties, filter by category/care/price, inspect plant care instructions, purchase with Cash on Delivery (COD) or Online payment, and track deliveries through a visual 5-stage timeline. Administrators have access to a dedicated management dashboard for catalog management, multiple image uploads, inventory stock adjustments, and order workflow handling.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13 / Flask 3.0.3, Jinja2, Werkzeug
- **Database**: SQLite 3 (`greeni5.db`) with Foreign Key constraints
- **Frontend**: HTML5, Modern CSS3 (CSS Variables, Flexbox, CSS Grid), Vanilla JavaScript (ES6+)
- **Icons**: Lucide Icons CDN
- **Images**: High-resolution curated botanical photography from Unsplash with local upload support
- **Design System**: Emerald and forest green nature theme, responsive layout across mobile, tablet, and desktop

---

## ✨ Features Overview

### 🛒 Customer Features
1. **Home Page**:
   - Hero banner with CTA buttons and key nursery guarantees
   - Plant categories showcase (Indoor, Outdoor, Flower, Fruit, Medicinal)
   - Curated Featured Plants & Best-Selling Varieties
   - Real customer testimonials and rating stars
2. **Plant Catalog & Live Filters**:
   - Filter by category tab
   - Filter by price range (Min & Max)
   - Filter by care difficulty level (Very Easy, Easy, Moderate)
   - Sort by Popularity, Price (Low to High / High to Low), Name, Newest
   - Live search by plant name or description
3. **Plant Details Page**:
   - Multi-image gallery with interactive thumbnail switcher
   - Detailed botanical information and descriptions
   - Structured Care Cards: **Sunlight, Watering, Temperature, Soil, Difficulty**
   - Live stock availability badge (In Stock / Low Stock / Out of Stock)
   - Quantity selector with dynamic stock upper bound
   - Customer reviews listing and "Write a Review" submission form
   - Related plants recommendation carousel
4. **Interactive Shopping Cart**:
   - Quantity stepper (+ / -) with instant subtotal and total updates
   - Dynamic Free Delivery progress bar (unlocks free shipping over ₹999)
   - 5% GST tax calculation and line-item deletion
5. **Checkout System**:
   - Shipping address and contact information form
   - One-click saved address autofill for authenticated customers
   - Payment options: **Cash on Delivery (COD)** and **Online / Card / UPI**
   - Stock auto-deduction upon order placement
   - Generates unique order tracking numbers (e.g. `GRN-2026-XXXX`)
6. **Live Order Tracking**:
   - Visual 5-stage progress timeline: `Pending` ➔ `Accepted` ➔ `Packed` ➔ `Shipped` ➔ `Delivered` (or `Rejected`)
   - Order lookup by tracking number
7. **Customer Dashboard**:
   - Personal profile editor (Name, Phone)
   - Complete order history with status pills and direct track buttons
   - Address book manager (Add / Delete saved shipping addresses)
8. **Informational & Support Pages**:
   - Plant Care Master Guide (`/care-tips`)
   - About Nursery Story & Greenhouse Guarantee (`/about`)
   - Contact Us form with database message storage (`/contact`)
   - Interactive FAQ accordion (`/faq`)

### 🛡️ Admin Features
1. **Secure Admin Portal (`/admin`)**:
   - Role-based authorization decorator (`@admin_required`)
2. **Admin Dashboard Metrics**:
   - Total Plants count
   - Total Registered Customers count
   - Total Orders count
   - Pending Orders alert counter
   - Lifetime Revenue overview
   - Recent customer orders table
   - Low-stock inventory alerts (< 10 units)
3. **Plant Catalog Management**:
   - Add new plant with pricing, discount, stock, care specifications, category
   - Multiple image uploads and image URL support
   - Edit existing plant information and manage gallery images
   - Delete plant
4. **Order Workflow Management**:
   - View all customer orders with item breakdown, customer phone, and shipping address
   - Filter by order status (`Pending`, `Accepted`, `Packed`, `Shipped`, `Delivered`, `Rejected`)
   - Update order status with automatic tracking reflection for customers
5. **Customer Directory**:
   - View all registered customers, contact numbers, order counts, and lifetime spend
6. **Inquiry Messages Center**:
   - View customer messages submitted via Contact Us page and mark as read

---

## 🔑 Pre-Seeded Demo Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@greeni5.com` | `Admin@123` | Full Admin Portal (`/admin`) & Storefront |
| **Customer** | `customer@greeni5.com` | `Customer@123` | Storefront, Cart, Checkout, Dashboard |

*(The login page includes convenient 1-Click buttons to autofill demo credentials)*

---

## 📁 Project Structure

```
greeni5/
├── app.py                      # Core Flask app, routing, session, cart, auth, admin API
├── database.py                 # SQLite database connection & execution utilities
├── schema.sql                  # Database schema definition (9 relational tables)
├── seed_data.py                # Database population script with 16+ curated plants
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── README.md                   # Full documentation and setup instructions
├── greeni5.db                  # Pre-seeded SQLite database file
├── static/
│   ├── css/
│   │   ├── style.css           # Customer stylesheet (green theme, responsive, cards, gallery)
│   │   └── admin.css           # Admin dashboard stylesheet (metrics, tables, badges)
│   ├── js/
│   │   ├── main.js             # Cart AJAX, toast notifications, gallery switcher, quantity
│   │   └── admin.js            # Admin status changer, multiple image preview
│   └── uploads/                # User uploaded plant images directory
└── templates/
    ├── base.html               # Main layout (topbar, navbar, search, cart badge, footer)
    ├── index.html              # Home page (Hero, Categories, Featured, Bestsellers, Reviews)
    ├── catalog.html            # Shop catalog (Filters, Sorting, Search, Responsive grid)
    ├── plant_details.html      # Details (Gallery, Care cards, Stock, Cart, Reviews)
    ├── cart.html               # Shopping cart with quantity stepper and free delivery bar
    ├── checkout.html           # Shipping info, payment selector, order review
    ├── order_success.html      # Order confirmation with invoice summary
    ├── order_tracking.html     # Live 5-stage timeline progress stepper
    ├── dashboard.html          # User profile, Order history with status, Saved addresses
    ├── login.html              # Authentication login with 1-click demo autofill
    ├── register.html           # Account registration
    ├── forgot_password.html    # Password reset flow simulation
    ├── care_tips.html          # Plant care guide (Watering, Sunlight, Soil, Feeding)
    ├── about.html              # Nursery story, greenhouse values, stats
    ├── contact.html            # Contact inquiry form & greenhouse location
    ├── faq.html                # Frequently asked questions
    └── admin/
        ├── base_admin.html     # Admin sidebar layout and topbar
        ├── dashboard.html      # Admin overview (Metrics, Recent orders, Low stock)
        ├── plants.html         # Plant catalog table with stock status and actions
        ├── plant_form.html     # Add / Edit plant form with multi-image handling
        ├── orders.html         # Order management with live status update
        ├── customers.html      # Customer directory with order counts and spend
        └── messages.html       # Customer contact messages center
```

---

## 🚀 Setup & Running Instructions

### 1. Prerequisites
- Python 3.10+ installed
- Flask (`python -m pip install flask`)

### 2. Navigate to Project Directory
```powershell
cd C:\Users\krish\.gemini\antigravity\scratch\greeni5
```

### 3. Initialize & Seed Database (Already performed, can be re-run anytime)
```powershell
python seed_data.py
```

### 4. Run the Flask Server
```powershell
python app.py
```

### 5. Access the Application
- Customer Storefront: **`http://127.0.0.1:5000`**
- Admin Portal: **`http://127.0.0.1:5000/admin`**
