# Quick Start Guide

## Initial Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Server**
   ```bash
   python manage.py runserver
   ```

5. **Access the Application**
   - Home: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Creating Test Data

### Via Admin Panel

1. Login to admin panel: http://127.0.0.1:8000/admin/
2. Create Categories:
   - Go to Categories
   - Add categories (e.g., "Pain Relief", "Antibiotics", "Vitamins")
   
3. Create Medicines:
   - Go to Medicines
   - Add medicines with:
     - Category, Name, SKU, Description, Salt
     - MRP, Price, Stock
     - Benefits (one per line in form)
     - How to Use (one per line)
     - Side Effects (one per line)
     - FAQs (Format: Question|Answer, one per line)
     - Image URL or Upload Image

### Via Registration

1. Register as Customer:
   - Go to http://127.0.0.1:8000/register/
   - Select role: Customer
   - Complete registration

2. Register as Pharmacist:
   - Go to http://127.0.0.1:8000/register/
   - Select role: Pharmacist
   - Complete registration

3. Register as Delivery Agent:
   - Go to http://127.0.0.1:8000/register/
   - Select role: Delivery Agent
   - Complete registration

## Testing the Application

### Customer Flow

1. Browse medicines (no login required)
2. View medicine details
3. Add items to cart (works without login, uses session)
4. Login/Register
5. View cart
6. Proceed to checkout
7. Add delivery address
8. Select payment method
9. Place order
10. View order history
11. Submit reviews for delivered orders

### Pharmacist Flow

1. Login as Pharmacist
2. View dashboard with analytics
3. Add/Edit/Delete medicines
4. View orders
5. Update order status

### Delivery Agent Flow

1. Login as Delivery Agent
2. View assigned orders
3. Update order status (Confirmed → Out for Delivery → Delivered)

## Important Notes

- Cart works for both authenticated and anonymous users (session-based)
- Checkout requires login
- Reviews can only be submitted by customers who have received the medicine
- Stock is automatically decremented when orders are placed
- Low stock alerts appear on pharmacist dashboard (stock < 10)

## Troubleshooting

### Profile not created
- If you create a user via admin, the profile will be created automatically via signals
- If issues occur, create profile manually in admin

### Cart not working
- Ensure sessions are enabled (default in Django)
- Check browser cookies are enabled

### Images not displaying
- Ensure MEDIA_URL and MEDIA_ROOT are configured correctly
- For production, configure static file serving properly

