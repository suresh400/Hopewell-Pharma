from .models import Cart, Notification


def cart_count(request):
    """Add cart count to all templates"""
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            cart_count = 0
    else:
        if request.session.session_key:
            try:
                cart = Cart.objects.get(session_key=request.session.session_key)
                cart_count = cart.get_total_items()
            except Cart.DoesNotExist:
                cart_count = 0
    
    return {'cart_count': cart_count}


def notification_count(request):
    """Add unread notification count to all templates"""
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return {'unread_notification_count': unread_count}


