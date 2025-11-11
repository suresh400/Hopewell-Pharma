from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Profile(models.Model):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('PHARMACIST', 'Pharmacist'),
        ('DELIVERY_AGENT', 'Delivery Agent'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image_url = models.URLField(max_length=10000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    supplier = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(blank=True, null=True)
    prescription_required = models.BooleanField(default=False)
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    image_url = models.URLField(max_length=10000, blank=True, null=True)
    # Additional images stored as JSON array of URLs
    additional_images = models.JSONField(default=list, blank=True)
    
    # JSON fields for lists
    benefits = models.JSONField(default=list, blank=True)
    how_to_use = models.JSONField(default=list, blank=True)
    side_effects = models.JSONField(default=list, blank=True)
    faqs = models.JSONField(default=list, blank=True)  # Format: [{"q": "question", "a": "answer"}]
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_image_url(self):
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None
    
    def is_low_stock(self):
        return self.stock < 10
    
    def get_discount_percentage(self):
        if self.mrp > self.price:
            discount = self.mrp - self.price
            return (discount / self.mrp) * 100
        return 0
    
    def get_all_images(self):
        """Get all images for the medicine"""
        images = []
        if self.get_image_url():
            images.append(self.get_image_url())
        if self.additional_images:
            images.extend(self.additional_images)
        return images


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['medicine', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.medicine.name} - {self.rating} stars"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.username}"
        return f"Cart - {self.session_key}"
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_subtotal(self):
        return sum(item.get_total() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'medicine']
    
    def __str__(self):
        return f"{self.medicine.name} x{self.quantity}"
    
    def get_total(self):
        return self.medicine.price * self.quantity


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('RAZORPAY', 'Razorpay (Online Payment)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='orders')
    delivery_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='assigned_orders', limit_choices_to={'profile__role': 'DELIVERY_AGENT'})
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    payment_ref = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-placed_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"
    
    def get_status_display_class(self):
        status_classes = {
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'CONFIRMED': 'bg-blue-100 text-blue-800',
            'OUT_FOR_DELIVERY': 'bg-purple-100 text-purple-800',
            'DELIVERED': 'bg-green-100 text-green-800',
            'CANCELLED': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.medicine.name if self.medicine else 'Deleted'} x{self.quantity}"
    
    def get_total(self):
        return self.price * self.quantity


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('NEW_ORDER', 'New Order'),
        ('ORDER_ACCEPTED', 'Order Accepted'),
        ('ORDER_OUT_FOR_DELIVERY', 'Order Out for Delivery'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('ORDER_STATUS_CHANGED', 'Order Status Changed'),
        ('LOW_STOCK', 'Low Stock Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    testimonial_text = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.rating} stars"
