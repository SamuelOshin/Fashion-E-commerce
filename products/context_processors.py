from .models import Product
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

def cart_details(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        total_price += product.price * quantity  # Accumulate total price for all products in the cart
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': product.price * quantity  # Total price for this product (price * quantity)
        })
    return {
        'cart_items': cart_items,
        'total_price': total_price  # Total price for all products in the cart
    }

def add_to_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    quantity = int(request.GET.get('quantity', 1))
    cart = request.session.get('cart', {})
    if str(product.id) in cart:
        cart[str(product.id)] += quantity
    else:
        cart[str(product.id)] = quantity
    request.session['cart'] = cart
    total_price = sum(Product.objects.get(id=int(pid)).price * qty for pid, qty in cart.items())
    return JsonResponse({'cart_count': sum(cart.values()), 'total_price': total_price})

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
    if str(product.id) in cart:
        cart[str(product.id)] = quantity
    else:
        cart[str(product.id)] = quantity
    request.session['cart'] = cart
    total_price = sum(Product.objects.get(id=int(pid)).price * qty for pid, qty in cart.items())
    item_total = product.price * quantity
    return JsonResponse({'cart_count': sum(cart.values()), 'total_price': float(total_price), 'item_total': float(item_total)})