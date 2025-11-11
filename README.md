# Online Pharmacy Web Application

A complete, production-ready Online Pharmacy Web Application built with Django, Tailwind CSS, and HTML templates. This application supports three user roles: Customer, Pharmacist, and Delivery Agent.

## Features

### Core Features

1. **Role-based Access Control**
   - Customer: Browse medicines, add to cart, place orders
   - Pharmacist: Manage medicines, view analytics, manage orders
   - Delivery Agent: View and update order delivery status

2. **Authentication**
   - User registration with role selection
   - Login/Logout functionality
   - Auto-login after registration
   - Role-based dashboard redirection

3. **Customer Features**
   - Browse medicines by category
   - Search medicines
   - View detailed medicine information (benefits, usage, side effects, FAQs)
   - Add to cart (AJAX)
   - View cart with quantity management
   - Checkout process (address + payment)
   - View order history
   - Submit reviews for purchased medicines

4. **Pharmacist Features**
   - Add/Edit/Delete medicines
   - Upload medicine images or use image URLs
   - Manage medicine details (benefits, usage, side effects, FAQs)
   - Dashboard with analytics:
     - Total orders, sales, delivered orders, customers
     - Low stock alerts
     - Sales chart (last 7 days)
   - Manage orders and update status

5. **Delivery Agent Features**
   - View assigned orders
   - Update order status (Pending → Out for Delivery → Delivered)

6. **Landing Page**
   - Banner with search bar
   - Horizontal scrolling categories
   - New launches section

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository** (or navigate to the project directory)

```bash
cd pharmacyweb
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
```

3. **Activate the virtual environment**

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create a superuser** (optional, for admin access)

```bash
python manage.py createsuperuser
```

7. **Run the development server**

```bash
python manage.py runserver
```

8. **Access the application**

   - Open your browser and go to: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Tailwind CSS Setup

This project uses Tailwind CSS via CDN. For production, you may want to set up Tailwind CSS with a build process:

1. **Install Tailwind CSS** (optional, for custom build)

```bash
npm install -D tailwindcss
npx tailwindcss init
```

2. **Configure Tailwind** (if using build process)

   Update `tailwind.config.js`:
   ```javascript
   content: [
       './pharmacy/templates/**/*.html',
   ]
   ```

3. **Current Setup**: The project uses Tailwind CSS via CDN in the base template, which is sufficient for development and small projects.

## Project Structure

```
pharmacyweb/
├── manage.py
├── requirements.txt
├── README.md
├── pharmacyweb/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── pharmacy/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── context_processors.py
    └── templates/
        └── pharmacy/
            ├── base.html
            ├── home.html
            ├── login.html
            ├── register.html
            ├── customer/
            │   ├── dashboard.html
            │   ├── medicine_detail.html
            │   ├── cart.html
            │   ├── checkout_step1.html
            │   ├── checkout_step2.html
            │   ├── order_success.html
            │   └── my_orders.html
            ├── pharmacist/
            │   ├── dashboard.html
            │   ├── medicine_list.html
            │   ├── medicine_form.html
            │   ├── medicine_delete.html
            │   └── orders.html
            └── delivery/
                └── dashboard.html
```

## Models

- **Profile**: User profile with role (Customer, Pharmacist, Delivery Agent)
- **Category**: Medicine categories
- **Medicine**: Medicine details with benefits, usage, side effects, FAQs
- **Review**: Customer reviews for medicines
- **Cart**: Shopping cart (user or session-based)
- **CartItem**: Items in the cart
- **Address**: Delivery addresses
- **Order**: Orders placed by customers
- **OrderItem**: Items in an order

## Usage

### Creating Test Data

1. **Access Django Admin**: `http://127.0.0.1:8000/admin/`
2. **Create Categories**: Add medicine categories
3. **Create Medicines**: Add medicines with all details
4. **Create Users**: Register users with different roles

### Testing the Application

1. **Register as Customer**: Browse medicines, add to cart, place orders
2. **Register as Pharmacist**: Add medicines, view analytics, manage orders
3. **Register as Delivery Agent**: View orders, update delivery status

## Important Notes

- **SECRET_KEY**: Change the SECRET_KEY in `settings.py` for production
- **DEBUG**: Set `DEBUG = False` in production
- **ALLOWED_HOSTS**: Update `ALLOWED_HOSTS` in `settings.py` for production
- **Database**: The project uses SQLite by default. For production, use PostgreSQL or MySQL
- **Static Files**: Run `python manage.py collectstatic` before deploying
- **Media Files**: Ensure media files are properly configured for production

## Payment Integration

The checkout process includes a placeholder for Razorpay integration. To integrate Razorpay:

1. Install Razorpay SDK: `pip install razorpay`
2. Add Razorpay keys to settings
3. Update the checkout view to handle Razorpay payments

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please create an issue in the repository.

## Acknowledgments

- Django Framework
- Tailwind CSS
- Chart.js for analytics

