# 🪷 Mithila White Gold
**Full-stack Django web application** for Mithila White Gold — premium makhana (fox nuts) from the heart of Mithila, Bihar.

> **मिथिला की धरोहर — हर कौर में।**

---

## 📋 Features

| Module | Features |
|---|---|
| 🌐 **Public Store** | Home, Product listing with filters, Product detail, Cart, Checkout |
| 👨‍🌾 **Farmer Auth** | Register, Login, My Orders, PDF Receipt download |
| 🛠️ **Admin Panel** | Django admin + Custom sales views + Site settings |
| 📄 **PDF Receipts** | ReportLab-generated receipt with GST, items table, company header |
| 📊 **Sales Records** | Manual walk-in sales, CSV export, filterable list |
| ⚙️ **Site Settings** | Admin-configurable email, phone, address |

---

## 🛠️ Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Django Templates + Bootstrap 5 + Custom CSS
- **PDF**: ReportLab
- **Forms**: django-crispy-forms + crispy-bootstrap5
- **Static Files**: WhiteNoise
- **Fonts**: Google Fonts — Hind + Poppins

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- pip

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Place the Logo

Copy your company logo image as:
```
static/img/logo.png
```
The provided logo image should be saved there.

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Seed Initial Data

```bash
python manage.py seed_data
```

This creates:
- ✅ 4 product categories
- ✅ 19 sample products (medicines, feed, chicks, equipment)
- ✅ Site settings (company info)
- ✅ Admin user: **admin / admin@123**

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## 🔑 Admin Access

| URL | Credentials |
|---|---|
| `/admin/` | admin / admin@123 |
| `/admin/sales/` | Custom sales records view |
| `/admin/sales/add/` | Add manual sale |
| `/admin/settings/` | Edit site settings |

---

## 🌐 URL Structure

```
/                          → Home
/products/                 → Product listing (with ?category=medicines|feed|chicks|equipment)
/products/<id>/            → Product detail
/cart/                     → Cart
/checkout/                 → Checkout (login required)
/orders/                   → My Orders (login required)
/orders/confirmation/<id>/ → Order confirmation
/receipt/<id>/pdf/         → Download order receipt PDF
/receipt/sales/<id>/pdf/   → Download sales receipt PDF

/login/                    → Farmer login
/register/                 → Farmer register
/logout/                   → Logout

/admin/                    → Django admin
/admin/sales/              → Custom sales list
/admin/sales/add/          → Add manual sale
/admin/settings/           → Site settings
```

---

## 🗄️ Models

| Model | Purpose |
|---|---|
| `SiteSettings` | Singleton — company email, phone, address |
| `Category` | Product categories (medicines, feed, chicks, equipment) |
| `Product` | Name, price, stock, image, category |
| `Farmer` | Extends User with phone and address |
| `Order` | Customer order with status tracking |
| `OrderItem` | Individual items in an order |
| `SalesRecord` | Manual walk-in sales record |
| `SalesItem` | Items within a sales record |
| `PaymentReceipt` | Auto-numbered receipt linked to Order or Sale |

---

## 🌿 Production Deployment (PostgreSQL)

Set environment variables in `.env`:

```
SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@host:5432/dbname
```

Then:
```bash
pip install dj-database-url psycopg2-binary
python manage.py migrate
python manage.py collectstatic
gunicorn poultry_farm.wsgi:application
```

---

## 🎨 Design

- **Colors**: Saffron `#FF8C00` | Forest Green `#2D6A4F` | Off-White `#FAF7F0`
- **Fonts**: Hind (Hindi/English bilingual) + Poppins (headings)
- **Responsive**: Mobile-first design for Bihar's farmers using phones

---

## 📞 Company Details

| Field | Value |
|---|---|
| Company | Mithila White Gold |
| Address | Darbhanga, Mithila, Bihar |
| Landmark | Near Darbhanga Tower |
| Satyam Jha | 6202822415 |
| GST | 10AAQFJ2396C1ZJ |
| Tagline | The Essence of Tradition in Every Crunch |
