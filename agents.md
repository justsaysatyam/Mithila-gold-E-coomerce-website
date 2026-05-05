# 🪷 Mithila White Gold - System Components & Agents Documentation

This document defines the roles, responsibilities, and workflows for the automated system agents and components involved in managing the Mithila White Gold online and offline operations.

---

## 1. 🛒 Public Store Management Agent

**Role:** Manages the public-facing e-commerce storefront and product discovery.
**Responsibilities:**
- Retrieve and display product catalogs (medicines, feed, chicks, equipment).
- Manage dynamic filtering based on product category.
- Handle shopping cart logic (add, remove, calculate totals).
- Process cart checkouts for authenticated customers.
**Key Interactions:** Reads from the `Product` and `Category` models, writes session-based cart data, and communicates with the Order Processing Agent upon checkout.

## 2. 👨‍🌾 Farmer Identity Agent

**Role:** Manages user authentication, security, and farmer-specific profile data.
**Responsibilities:**
- Handle secure registration, login, and session management.
- Link Django Auth users to `Farmer` profiles containing contact numbers and addresses.
- Enforce access control for private areas like "My Orders" and checkout.
**Key Interactions:** Interfaces with Django Auth and the `Farmer` model.

## 3. 📦 Order Fulfillment Agent

**Role:** Tracks and manages the lifecycle of customer online orders.
**Responsibilities:**
- Process new `Order` and associated `OrderItem` entries.
- Maintain order statuses (e.g., Pending, Delivered) for the admin and customer.
- Communicate with the Document Generation Agent to trigger order confirmation PDFs.
**Key Interactions:** Reads user ID and cart items; creates `Order` and `PaymentReceipt` records.

## 4. 🏪 Point-of-Sale (Walk-in) Agent

**Role:** Facilitates administrative manual sales at the physical shop/feeding point.
**Responsibilities:**
- Provide a streamlined custom admin interface (`/admin/sales/add/`) for manual billing.
- Record `SalesRecord` and `SalesItem` entries directly, bypassing the online cart.
- Support CSV exports for offline sales analysis.
**Key Interactions:** Exclusively accessible by the Admin (`Satyam Jha`). Triggers walk-in specific receipts.

## 5. 📄 Document Generation Agent (ReportLab)

**Role:** Automates the generation of compliant PDF invoices and receipts.
**Responsibilities:**
- Utilize `ReportLab` to structure professional PDF layouts dynamically.
- Include mandatory business details: GST Number (`10AAQFJ2396C1ZJ`), Company Header, and Contact logic.
- Serve tailored receipts for both online Orders (`/receipt/<id>/pdf/`) and manual Sales (`/receipt/sales/<id>/pdf/`).
**Key Interactions:** Fetches live company details from `SiteSettings` and sequential indexing from `PaymentReceipt`.

## 6. ⚙️ Global Configuration Agent

**Role:** Manages the centralized deployment and singleton settings of the platform.
**Responsibilities:**
- Manage dynamic company information (Email, Phone, Address, Landmark).
- Serve context variables across all Django templates globally.
- Serve as the interface for admins to update store contact info without codebase changes.
**Key Interactions:** Manages the `SiteSettings` singleton model and injects state into views and context processors.
