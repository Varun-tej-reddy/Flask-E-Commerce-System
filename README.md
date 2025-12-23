# Flask-E-Commerce-System
This is a Flask-based e‑commerce web application built as a college project. It includes user authentication, admin product management, product image upload, and MySQL database integration.  The project is structured in a clean, modular way using Flask best practices.










Project Structure

web_project/
│── run.py                # Application entry point
│── config.py             # App & database configuration
│── seed_admin.py         # Creates default admin account
├── app/
│   ├── __init__.py           # App factory
│   ├── models.py             # Database models
│   ├── forms.py              # Flask-WTF forms
│   ├── routes.py             # All application routes
│   ├── templates/
│        ├── login.html        # Login page
│        ├── add_product.html  # Add product page
│   ├── static/
│       ├── upload/           # stores uploaded product images
│
│   ├── templates/
│   ├──add_product.html
│   ├──admin_dashboard.html
│   ├──admin_orders.html
│   ├──base.html
│   ├──cart.html
│   ├──checkout.html
│   ├──edit_product.html
│   ├──login.html
│   ├──manage_products.html
│   ├──orders.html
│   ├──register.html
│   ├──settings.html
        └──user_dashboard.html
