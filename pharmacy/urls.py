from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Customer routes
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('medicine/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/step1/', views.checkout_step1, name='checkout_step1'),
    path('checkout/step2/<int:address_id>/', views.checkout_step2, name='checkout_step2'),
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Pharmacist routes
    path('pharmacist/dashboard/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('pharmacist/medicines/', views.medicine_list, name='medicine_list'),
    path('pharmacist/medicines/add/', views.medicine_add, name='medicine_add'),
    path('pharmacist/medicines/edit/<int:pk>/', views.medicine_edit, name='medicine_edit'),
    path('pharmacist/medicines/delete/<int:pk>/', views.medicine_delete, name='medicine_delete'),
    path('pharmacist/orders/', views.pharmacist_orders, name='pharmacist_orders'),
    path('pharmacist/orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('pharmacist/categories/', views.category_list, name='category_list'),
    path('pharmacist/categories/add/', views.category_add, name='category_add'),
    path('pharmacist/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('pharmacist/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Delivery Agent routes
    path('delivery/dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/orders/accept/<int:order_id>/', views.accept_order, name='accept_order'),
    path('delivery/orders/reject/<int:order_id>/', views.reject_order, name='reject_order'),
    path('delivery/orders/update/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Profile
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Delivery Agent Management (Pharmacist only)
    path('pharmacist/delivery-agent/add/', views.add_delivery_agent, name='add_delivery_agent'),
    
    # Testimonials
    path('pharmacist/testimonials/', views.testimonial_list, name='testimonial_list'),
    path('pharmacist/testimonials/add/', views.testimonial_add, name='testimonial_add'),
    path('pharmacist/testimonials/edit/<int:pk>/', views.testimonial_edit, name='testimonial_edit'),
    path('pharmacist/testimonials/delete/<int:pk>/', views.testimonial_delete, name='testimonial_delete'),
    path('pharmacist/testimonials/approve/<int:pk>/', views.testimonial_approve, name='testimonial_approve'),
    
    # API
    path('api/search-medicines/', views.search_medicines_api, name='search_medicines_api'),
    
    # Razorpay
    path('razorpay/create-order/<int:order_id>/', views.create_razorpay_order, name='create_razorpay_order'),
    path('razorpay/success/<int:order_id>/', views.razorpay_success, name='razorpay_success'),
]

