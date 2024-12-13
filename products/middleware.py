# products/middleware.py

from django.utils.deprecation import MiddlewareMixin

class CartCleanupMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cart = request.session.get('cart', {})
        updated = False
        for product_id, item in cart.items():
            if isinstance(item, int):
                # Reset to proper structure
                cart[product_id] = {
                    'quantity': item,
                    'sizes': [],
                    'colors': []
                }
                updated = True
        if updated:
            request.session['cart'] = cart