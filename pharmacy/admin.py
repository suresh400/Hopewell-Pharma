from django.contrib import admin
from .models import (
    Profile, Category, Medicine, Review, Cart, CartItem,
    Address, Order, OrderItem, Notification, Testimonial
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'prescription_required', 'created_at']
    list_filter = ['category', 'prescription_required', 'created_at']
    search_fields = ['name', 'sku', 'supplier']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['medicine__name', 'user__username']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'created_at']
    search_fields = ['user__username', 'session_key']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'medicine', 'quantity', 'created_at']
    search_fields = ['medicine__name', 'cart__user__username']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'pincode', 'is_default', 'created_at']
    list_filter = ['city', 'state', 'is_default']
    search_fields = ['user__username', 'full_name', 'city', 'pincode']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'payment_method', 'placed_at']
    list_filter = ['status', 'payment_method', 'placed_at']
    search_fields = ['user__username', 'payment_ref']
    readonly_fields = ['placed_at', 'updated_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'medicine', 'quantity', 'price']
    search_fields = ['order__id', 'medicine__name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['customer_name', 'customer_email', 'testimonial_text']
    readonly_fields = ['created_at']


