from decimal import Decimal
from .models import Product
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Order, OrderItem
from django.shortcuts import get_object_or_404, redirect
import json

def cart_details(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    cart_count = 0

    for product_id, items in cart.items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue  # Skip items with invalid products

        for item in items:
            quantity = int(item.get('quantity', 0))
            size = item.get('size', '')
            color = item.get('color', '')
            item_total = product.price * Decimal(quantity)
            total_price += item_total
            cart_count += quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': item_total,
                'size': size,
                'color': color
            })

    return {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count
    }

@csrf_exempt
def add_to_cart(request, product_slug):
    if request.method == 'POST':
        data = json.loads(request.body)
        sizes = data.get('sizes', [])
        colors = data.get('colors', [])
        quantity = int(data.get('quantity', 1))  # Ensure quantity is an integer

        if not sizes or not colors:
            return JsonResponse({'success': False, 'message': 'Please select at least one size and one color.'})

        try:
            product = Product.objects.get(slug=product_slug)
            cart = request.session.get('cart', {})
            if str(product.id) in cart:
                cart[str(product.id)]['quantity'] += quantity
                cart[str(product.id)]['sizes'].extend(sizes)
                cart[str(product.id)]['colors'].extend(colors)
            else:
                cart[str(product.id)] = {
                    'quantity': quantity,
                    'sizes': sizes,
                    'colors': colors
                }
            request.session['cart'] = cart
            total_price = sum(Product.objects.get(id=int(pid)).price * Decimal(item['quantity']) for pid, item in cart.items())
            cart_count = sum(item['quantity'] for item in cart.values())
            return JsonResponse({'cart_count': cart_count, 'total_price': total_price, 'success': True, 'message': 'Product added to cart successfully.'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product does not exist.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
def remove_from_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    cart = request.session.get('cart', {})
    if str(product.id) in cart:
        del cart[str(product.id)]
        request.session['cart'] = cart
    return redirect('cart_detail')

def update_cart_item(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    quantity = int(request.GET.get('quantity', 1))
    cart = request.session.get('cart', {})
    product_id_str = str(product.id)
    
    if product_id_str in cart:
        if isinstance(cart[product_id_str], dict):
            cart[product_id_str]['quantity'] = quantity
        else:
            # Reset to proper structure if it's not a dict
            cart[product_id_str] = {
                'quantity': quantity,
                'sizes': [],
                'colors': []
            }
    else:
        cart[product_id_str] = {
            'quantity': quantity,
            'sizes': [],
            'colors': []
        }
    
    request.session['cart'] = cart
    
    # Calculate total_price correctly
    total_price = sum(
        Product.objects.get(id=int(pid)).price * Decimal(item['quantity'])
        for pid, item in cart.items()
        if isinstance(item, dict)
    )
    
    item_total = product.price * Decimal(quantity)
    
    return JsonResponse({
        'cart_count': sum(item['quantity'] for item in cart.values() if isinstance(item, dict)),
        'total_price': float(total_price),
        'item_total': float(item_total)
    })