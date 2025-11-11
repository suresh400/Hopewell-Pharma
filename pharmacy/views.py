from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import razorpay
from decimal import Decimal
import json

from .models import (
    Profile, Category, Medicine, Review, Cart, CartItem,
    Address, Order, OrderItem, Notification, Testimonial
)
from .forms import UserRegisterForm, MedicineForm, AddressForm, ReviewForm, CategoryForm


# ==================== AUTHENTICATION ====================

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data.get('email')
            user.save()
            
            # Update profile (created by signal, use get_or_create as safety)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = form.cleaned_data.get('role')
            profile.phone = form.cleaned_data.get('phone')
            profile.save()
            
            # Auto-login
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Account created successfully! Welcome, {username}!')
                return redirect('home')  # Redirect to landing page
    else:
        form = UserRegisterForm()
    return render(request, 'pharmacy/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            # Redirect delivery agents directly to delivery dashboard
            if hasattr(user, 'profile') and user.profile.role == 'DELIVERY_AGENT':
                return redirect('delivery_dashboard')
            return redirect('home')  # Redirect to landing page
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'pharmacy/login.html')


@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# ==================== DASHBOARD REDIRECT ====================

@login_required
def dashboard(request):
    profile = request.user.profile
    role = profile.role
    
    if role == 'CUSTOMER':
        return redirect('customer_dashboard')
    elif role == 'PHARMACIST':
        return redirect('pharmacist_dashboard')
    elif role == 'DELIVERY_AGENT':
        return redirect('delivery_dashboard')
    else:
        return redirect('home')


# ==================== LANDING PAGE ====================

def home(request):
    categories = Category.objects.all()[:8]
    new_launches = Medicine.objects.filter(stock__gt=0).order_by('-created_at')[:8]
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:6]
    return render(request, 'pharmacy/home.html', {
        'categories': categories,
        'new_launches': new_launches,
        'testimonials': testimonials,
    })


# ==================== CUSTOMER VIEWS ====================

def customer_dashboard(request):
    # Allow anyone to browse medicines, but check role if authenticated
    if request.user.is_authenticated and request.user.profile.role != 'CUSTOMER':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    categories = Category.objects.all()
    medicines = Medicine.objects.filter(stock__gt=0)
    
    # Search functionality
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(supplier__icontains=query)
        )
    
    if category_id:
        medicines = medicines.filter(category_id=category_id)
    
    return render(request, 'pharmacy/customer/dashboard.html', {
        'medicines': medicines,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })


def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    reviews = Review.objects.filter(medicine=medicine)
    can_review = False
    
    if request.user.is_authenticated:
        # Check if user has ordered this medicine
        has_ordered = OrderItem.objects.filter(
            order__user=request.user,
            medicine=medicine,
            order__status='DELIVERED'
        ).exists()
        can_review = has_ordered and not reviews.filter(user=request.user).exists()
    
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid() and can_review:
            review = review_form.save(commit=False)
            review.medicine = medicine
            review.user = request.user
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('medicine_detail', pk=pk)
    else:
        review_form = ReviewForm()
    
    return render(request, 'pharmacy/customer/medicine_detail.html', {
        'medicine': medicine,
        'reviews': reviews,
        'review_form': review_form,
        'can_review': can_review,
    })


# ==================== CART VIEWS ====================

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(session_key=request.session.session_key)
    return cart


@require_POST
def add_to_cart(request):
    """Add item to cart via AJAX"""
    try:
        medicine_id = request.POST.get('medicine_id')
        quantity = int(request.POST.get('quantity', 1))
        
        medicine = get_object_or_404(Medicine, pk=medicine_id)
        
        if medicine.stock < quantity:
            return JsonResponse({'success': False, 'message': 'Insufficient stock'})
        
        cart = get_or_create_cart(request)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            medicine=medicine,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > medicine.stock:
                cart_item.quantity = medicine.stock
            cart_item.save()
        
        cart_count = cart.get_total_items()
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_count': cart_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    subtotal = cart.get_subtotal()
    tax = subtotal * Decimal('0.05')  # 5% GST
    total = subtotal + tax
    
    return render(request, 'pharmacy/customer/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    })


@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    action = request.POST.get('action')
    
    if action == 'increase':
        if cart_item.quantity < cart_item.medicine.stock:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
    
    cart = cart_item.cart
    subtotal = cart.get_subtotal()
    tax = subtotal * Decimal('0.05')
    total = subtotal + tax
    
    return JsonResponse({
        'success': True,
        'quantity': cart_item.quantity,
        'item_total': float(cart_item.get_total()),
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total),
        'cart_count': cart.get_total_items(),
    })


@require_POST
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    cart_item.delete()
    
    # Re-fetch cart to get updated totals
    cart.refresh_from_db()
    subtotal = cart.get_subtotal()
    tax = subtotal * Decimal('0.05')
    total = subtotal + tax
    
    return JsonResponse({
        'success': True,
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total),
        'cart_count': cart.get_total_items(),
    })


# ==================== CHECKOUT VIEWS ====================

def checkout_step1(request):
    """Delivery Address Form"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to continue checkout.')
        return redirect('login')
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            address.save()
            return redirect('checkout_step2', address_id=address.id)
    else:
        form = AddressForm()
    
    return render(request, 'pharmacy/customer/checkout_step1.html', {
        'form': form,
        'addresses': addresses,
    })


def checkout_step2(request, address_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to continue checkout.')
        return redirect('login')

    address = get_object_or_404(Address, pk=address_id, user=request.user)
    cart = get_or_create_cart(request)

    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    subtotal = cart.get_subtotal()
    tax = subtotal * Decimal('0.05')
    total = subtotal + tax

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        # ==== RAZORPAY PAYMENT ====
        if payment_method == 'RAZORPAY':
            # STEP 1: Create order in our DB
            order = Order.objects.create(
                user=request.user,
                address=address,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_method=payment_method,
                status='PENDING'
            )

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=cart_item.medicine,
                    quantity=cart_item.quantity,
                    price=cart_item.medicine.price
                )

            # STEP 2: Create Razorpay Order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                "amount": int(order.total * 100),   # Convert to paise
                "currency": "INR",
                "payment_capture": "1",
            })

            # STEP 3: Save Razorpay order id in DB
            order.razorpay_order_id = razorpay_order['id']
            order.save()

            return render(request, "pharmacy/customer/razorpay_payment.html", {
                "order": order,
                "razorpay_order_id": order.razorpay_order_id,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": int(order.total * 100),
                "user": request.user
            })

        # ==== CASH ON DELIVERY ====
        else:
            order = Order.objects.create(
                user=request.user,
                address=address,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_method=payment_method,
                status='PENDING',
            )

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=cart_item.medicine,
                    quantity=cart_item.quantity,
                    price=cart_item.medicine.price
                )
                cart_item.medicine.stock -= cart_item.quantity
                cart_item.medicine.save()

            cart.items.all().delete()

            messages.success(request, 'Order placed successfully!')
            return redirect('order_success', order_id=order.id)

    return render(request, 'pharmacy/customer/checkout_step2.html', {
        'address': address,
        'cart_items': cart.items.all(),
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    })

def order_success(request, order_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view order.')
        return redirect('login')
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'pharmacy/customer/order_success.html', {
        'order': order,
    })

def payment_success(request, order_id):
    order = Order.objects.get(id=order_id)
    # Clear cart
    CartItem.objects.filter(cart__user=request.user).delete()
    order.status = "CONFIRMED"
    order.save()
    return render(request, "pharmacy/customer/order_success.html", {"order": order})


def my_orders(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view orders.')
        return redirect('login')
    orders = Order.objects.filter(user=request.user).order_by('-placed_at')
    return render(request, 'pharmacy/customer/my_orders.html', {
        'orders': orders,
    })


# ==================== PHARMACIST VIEWS ====================

@login_required
def pharmacist_dashboard(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Analytics
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status='DELIVERED').aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    total_sales = round(total_sales, 2)  # Ensure 2 decimal places
    delivered_orders = Order.objects.filter(status='DELIVERED').count()
    total_customers = User.objects.filter(profile__role='CUSTOMER').count()
    
    # Low stock alerts
    low_stock_medicines = Medicine.objects.filter(stock__lt=10)
    
    # Last 7 days sales data for chart
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)
    
    sales_data = []
    labels = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        daily_sales = Order.objects.filter(
            status='DELIVERED',
            placed_at__date=date
        ).aggregate(Sum('total'))['total__sum'] or 0
        sales_data.append(float(daily_sales))
        labels.append(date.strftime('%d %b'))
    
    # Customer details with order counts
    customers = User.objects.filter(profile__role='CUSTOMER').select_related('profile').order_by('-date_joined')[:10]
    customers_with_orders = []
    for customer in customers:
        order_count = Order.objects.filter(user=customer).count()
        customers_with_orders.append({
            'user': customer,
            'order_count': order_count,
        })
    
    # Delivery agent details with order counts
    delivery_agents = User.objects.filter(profile__role='DELIVERY_AGENT').select_related('profile').order_by('-date_joined')
    agents_with_orders = []
    for agent in delivery_agents:
        total_orders = Order.objects.filter(delivery_agent=agent).count()
        delivered_orders = Order.objects.filter(delivery_agent=agent, status='DELIVERED').count()
        agents_with_orders.append({
            'user': agent,
            'total_orders': total_orders,
            'delivered_orders': delivered_orders,
        })
    
    return render(request, 'pharmacy/pharmacist/dashboard.html', {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'delivered_orders': delivered_orders,
        'total_customers': total_customers,
        'low_stock_medicines': low_stock_medicines,
        'sales_data': json.dumps(sales_data),
        'sales_labels': json.dumps(labels),
        'customers_with_orders': customers_with_orders,
        'agents_with_orders': agents_with_orders,
    })


@login_required
def medicine_list(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    medicines = Medicine.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query) |
            Q(supplier__icontains=query)
        )
    
    return render(request, 'pharmacy/pharmacist/medicine_list.html', {
        'medicines': medicines,
        'query': query,
    })


@login_required
def medicine_add(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        # Collect additional images from dynamic fields
        additional_images = []
        i = 0
        while f'additional_image_{i}' in request.POST:
            url = request.POST.get(f'additional_image_{i}', '').strip()
            if url:
                additional_images.append(url)
            i += 1
        
        if form.is_valid():
            medicine = form.save()
            # Override additional_images if provided via dynamic fields
            if additional_images:
                medicine.additional_images = additional_images
                medicine.save()
            messages.success(request, 'Medicine added successfully!')
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    
    return render(request, 'pharmacy/pharmacist/medicine_form.html', {
        'form': form,
        'medicine': None,
        'title': 'Add Medicine',
    })


@login_required
def medicine_edit(request, pk):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        # Collect additional images from dynamic fields
        additional_images = []
        i = 0
        while f'additional_image_{i}' in request.POST:
            url = request.POST.get(f'additional_image_{i}', '').strip()
            if url:
                additional_images.append(url)
            i += 1
        
        if form.is_valid():
            medicine = form.save()
            # Override additional_images if provided via dynamic fields
            if additional_images:
                medicine.additional_images = additional_images
                medicine.save()
            messages.success(request, 'Medicine updated successfully!')
            return redirect('medicine_list')
    else:
        # Pre-populate form fields
        form = MedicineForm(instance=medicine)
        form.fields['benefits_json'].initial = '\n'.join(medicine.benefits)
        form.fields['how_to_use_json'].initial = '\n'.join(medicine.how_to_use)
        form.fields['side_effects_json'].initial = '\n'.join(medicine.side_effects)
        faqs_text = '\n'.join([f"{faq.get('q', '')}|{faq.get('a', '')}" for faq in medicine.faqs])
        form.fields['faqs_json'].initial = faqs_text
        form.fields['additional_images_json'].initial = '\n'.join(medicine.additional_images)
    
    return render(request, 'pharmacy/pharmacist/medicine_form.html', {
        'form': form,
        'medicine': medicine,
        'title': 'Edit Medicine',
    })


@login_required
def medicine_delete(request, pk):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, 'Medicine deleted successfully!')
        return redirect('medicine_list')
    
    return render(request, 'pharmacy/pharmacist/medicine_delete.html', {
        'medicine': medicine,
    })


@login_required
def pharmacist_orders(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    orders = Order.objects.all().order_by('-placed_at')
    status_filter = request.GET.get('status')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    return render(request, 'pharmacy/pharmacist/orders.html', {
        'orders': orders,
        'status_filter': status_filter,
    })


@login_required
def update_order_status(request, order_id):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully!')
        return redirect('pharmacist_orders')
    
    return redirect('pharmacist_orders')


# ==================== CATEGORY MANAGEMENT ====================

@login_required
def category_list(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    categories = Category.objects.all().order_by('name')
    return render(request, 'pharmacy/pharmacist/category_list.html', {
        'categories': categories,
    })


@login_required
def category_add(request):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'pharmacy/pharmacist/category_form.html', {
        'form': form,
        'title': 'Add Category',
    })


@login_required
def category_edit(request, pk):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'pharmacy/pharmacist/category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
    })


@login_required
def category_delete(request, pk):
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    
    return render(request, 'pharmacy/pharmacist/category_delete.html', {
        'category': category,
    })


# ==================== DELIVERY AGENT VIEWS ====================

@login_required
def delivery_dashboard(request):
    if request.user.profile.role != 'DELIVERY_AGENT':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    status_filter = request.GET.get('status')
    
    # Get orders available for acceptance (PENDING or CONFIRMED and not assigned to anyone)
    if status_filter:
        available_orders = Order.objects.filter(
            status=status_filter,
            delivery_agent__isnull=True
        ).select_related('user', 'address').prefetch_related('items__medicine').order_by('-placed_at')
    else:
        available_orders = Order.objects.filter(
            status__in=['PENDING', 'CONFIRMED'],
            delivery_agent__isnull=True
        ).select_related('user', 'address').prefetch_related('items__medicine').order_by('-placed_at')
    
    # Get orders assigned to this delivery agent
    if status_filter:
        my_orders = Order.objects.filter(
            delivery_agent=request.user,
            status=status_filter
        ).select_related('user', 'address').prefetch_related('items__medicine').order_by('-placed_at')
    else:
        my_orders = Order.objects.filter(
            delivery_agent=request.user
        ).select_related('user', 'address').prefetch_related('items__medicine').order_by('-placed_at')
    
    return render(request, 'pharmacy/delivery/dashboard.html', {
        'available_orders': available_orders,
        'my_orders': my_orders,
        'status_filter': status_filter,
    })


@login_required
def accept_order(request, order_id):
    """Delivery agent accepts an order"""
    if request.user.profile.role != 'DELIVERY_AGENT':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    order = get_object_or_404(Order, pk=order_id, status__in=['PENDING', 'CONFIRMED'], delivery_agent__isnull=True)
    
    if request.method == 'POST':
        order.delivery_agent = request.user
        # If order is PENDING, automatically confirm it when accepted
        if order.status == 'PENDING':
            order.status = 'CONFIRMED'
        order.save()
        
        # Create notification for customer
        Notification.objects.create(
            user=order.user,
            notification_type='ORDER_ACCEPTED',
            title='Order Accepted',
            message=f'Your order #{order.id} has been accepted by delivery agent {request.user.username}. It will be delivered soon.',
            order=order
        )
        
        messages.success(request, f'Order #{order.id} accepted successfully!')
        return redirect('delivery_dashboard')
    
    return redirect('delivery_dashboard')


@login_required
def reject_order(request, order_id):
    """Delivery agent rejects an order (optional - can skip if not needed)"""
    if request.user.profile.role != 'DELIVERY_AGENT':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    order = get_object_or_404(Order, pk=order_id, delivery_agent=request.user)
    
    if request.method == 'POST':
        order.delivery_agent = None
        order.save()
        messages.success(request, f'Order #{order.id} rejected and made available for other agents.')
        return redirect('delivery_dashboard')
    
    return redirect('delivery_dashboard')


@login_required
def update_delivery_status(request, order_id):
    """Update order status for accepted orders"""
    if request.user.profile.role != 'DELIVERY_AGENT':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    order = get_object_or_404(Order, pk=order_id, delivery_agent=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['OUT_FOR_DELIVERY', 'DELIVERED']:
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Create notification for customer
            if new_status == 'OUT_FOR_DELIVERY':
                Notification.objects.create(
                    user=order.user,
                    notification_type='ORDER_OUT_FOR_DELIVERY',
                    title='Order Out for Delivery',
                    message=f'Your order #{order.id} is out for delivery. Delivery agent: {request.user.username}. Expected delivery soon.',
                    order=order
                )
            elif new_status == 'DELIVERED':
                Notification.objects.create(
                    user=order.user,
                    notification_type='ORDER_DELIVERED',
                    title='Order Delivered',
                    message=f'Your order #{order.id} has been delivered successfully by {request.user.username}. Thank you for your purchase!',
                    order=order
                )
            
            messages.success(request, 'Order status updated successfully!')
        return redirect('delivery_dashboard')
    
    return redirect('delivery_dashboard')


# ==================== NOTIFICATIONS ====================

@login_required
def notifications_list(request):
    """View all notifications for the logged-in user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'pharmacy/notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications_list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_list')


# ==================== PROFILE ====================

@login_required
def profile_view(request):
    """View and edit user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update user info
        request.user.email = request.POST.get('email', request.user.email)
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()
        
        # Update profile
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile_view')
    
    return render(request, 'pharmacy/profile.html', {
        'profile': profile,
    })


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'Password changed successfully! Please login again.')
        return redirect('login')
    
    return render(request, 'pharmacy/change_password.html')


# ==================== DELIVERY AGENT REGISTRATION ====================

@login_required
def add_delivery_agent(request):
    """Add delivery agent (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data.get('email')
            user.save()
            
            # Update profile to DELIVERY_AGENT (override the role from form)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = 'DELIVERY_AGENT'
            profile.phone = form.cleaned_data.get('phone')
            profile.save()
            
            messages.success(request, f'Delivery agent {user.username} created successfully!')
            return redirect('pharmacist_dashboard')
    else:
        form = UserRegisterForm()
    
    return render(request, 'pharmacy/pharmacist/add_delivery_agent.html', {
        'form': form,
    })


# ==================== TESTIMONIALS ====================

@login_required
def testimonial_list(request):
    """List all testimonials (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    testimonials = Testimonial.objects.all().order_by('-created_at')
    return render(request, 'pharmacy/pharmacist/testimonial_list.html', {
        'testimonials': testimonials,
    })


@login_required
def testimonial_add(request):
    """Add new testimonial (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email', '')
        rating = int(request.POST.get('rating', 5))
        testimonial_text = request.POST.get('testimonial_text')
        is_approved = request.POST.get('is_approved') == 'on'
        
        Testimonial.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            rating=rating,
            testimonial_text=testimonial_text,
            is_approved=is_approved
        )
        messages.success(request, 'Testimonial added successfully!')
        return redirect('testimonial_list')
    
    return render(request, 'pharmacy/pharmacist/testimonial_form.html', {
        'testimonial': None,
        'title': 'Add Testimonial',
    })


@login_required
def testimonial_edit(request, pk):
    """Edit testimonial (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        testimonial.customer_name = request.POST.get('customer_name')
        testimonial.customer_email = request.POST.get('customer_email', '')
        testimonial.rating = int(request.POST.get('rating', 5))
        testimonial.testimonial_text = request.POST.get('testimonial_text')
        testimonial.is_approved = request.POST.get('is_approved') == 'on'
        testimonial.save()
        messages.success(request, 'Testimonial updated successfully!')
        return redirect('testimonial_list')
    
    return render(request, 'pharmacy/pharmacist/testimonial_form.html', {
        'testimonial': testimonial,
        'title': 'Edit Testimonial',
    })


@login_required
def testimonial_delete(request, pk):
    """Delete testimonial (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        testimonial.delete()
        messages.success(request, 'Testimonial deleted successfully!')
        return redirect('testimonial_list')
    
    return render(request, 'pharmacy/pharmacist/testimonial_delete.html', {
        'testimonial': testimonial,
    })


@login_required
def testimonial_approve(request, pk):
    """Approve/unapprove testimonial (Pharmacist only)"""
    if request.user.profile.role != 'PHARMACIST':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.is_approved = not testimonial.is_approved
    testimonial.save()
    
    status = 'approved' if testimonial.is_approved else 'unapproved'
    messages.success(request, f'Testimonial {status} successfully!')
    return redirect('testimonial_list')


# ==================== API ====================

def search_medicines_api(request):
    """API endpoint for search dropdown"""
    query = request.GET.get('q', '').strip()
    
    if len(query) > 0:
        medicines = Medicine.objects.filter(
            Q(name__istartswith=query) | Q(name__icontains=query)
        ).filter(stock__gt=0)[:10]
        
        results = [{
            'id': med.id,
            'name': med.name,
            'price': str(med.price),
        } for med in medicines]
        
        return JsonResponse({'medicines': results})
    
    return JsonResponse({'medicines': []})


# ==================== RAZORPAY PAYMENT ====================

@login_required
def create_razorpay_order(request, order_id):
    """Create Razorpay order"""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        razorpay_order = client.order.create({
            'amount': int(order.total * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': f'order_{order.id}',
            'notes': {
                'order_id': order.id,
            }
        })
        
        # Save razorpay order ID
        order.payment_ref = razorpay_order['id']
        order.save()
        
        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def razorpay_success(request, order_id):
    """Handle Razorpay payment success"""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    
    payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')
    
    # Verify signature
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        client.utility.verify_payment_signature(params_dict)
        
        # Payment verified - update order
        order.payment_ref = payment_id
        order.status = 'CONFIRMED'
        order.save()
        
        # Update stock
        for item in order.items.all():
            item.medicine.stock -= item.quantity
            item.medicine.save()
        
        # Clear cart
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        
        # Create notifications
        Notification.objects.create(
            user=request.user,
            notification_type='NEW_ORDER',
            title='Order Placed Successfully',
            message=f'Your order #{order.id} has been placed successfully. Payment received via Razorpay. Total: ₹{order.total}.',
            order=order
        )
        
        delivery_agents = User.objects.filter(profile__role='DELIVERY_AGENT')
        for agent in delivery_agents:
            Notification.objects.create(
                user=agent,
                notification_type='NEW_ORDER',
                title='New Order Available',
                message=f'New order #{order.id} from {order.user.username}. Address: {order.address.city}, {order.address.state}. Total: ₹{order.total}. Payment: Razorpay.',
                order=order
            )
        
        pharmacists = User.objects.filter(profile__role='PHARMACIST')
        for pharmacist in pharmacists:
            Notification.objects.create(
                user=pharmacist,
                notification_type='NEW_ORDER',
                title='New Order Received',
                message=f'New order #{order.id} from {order.user.username}. Total: ₹{order.total}. Payment: Razorpay.',
                order=order
            )
        
        messages.success(request, 'Payment successful! Order placed successfully.')
        return redirect('order_success', order_id=order.id)
        
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('checkout_step1')
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('checkout_step1')


