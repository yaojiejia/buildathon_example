business_case/ is a small demo e-commerce backend + simple UI for placing and refunding orders.

In plain terms, it does this:

Runs a FastAPI app (main.py) with a SQLite DB (shop.db).
Seeds demo data on startup: products, customers, promo codes.
Serves a web page (index.html) where you can:
view products/customers/orders
place an order
refund an order
Exposes API routes (routes.py) for:
GET /api/products
GET /api/customers
POST /api/orders
GET /api/orders
POST /api/refunds
GET /api/promo-codes
Uses SQLAlchemy models (models.py) for Product, Customer, Order, OrderItem, and PromoCode.
Business logic lives in services.py:
validates stock
calculates discounts
updates loyalty points/tier
processes refunds
Sends logs/events to Sentry if SENTRY_DSN is configured.
