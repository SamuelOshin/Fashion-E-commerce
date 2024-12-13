from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, GalleryMedia, Cart, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CheckoutForm, LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail

from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.contrib import messages
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)

def index(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    context = {
        'categories': categories,
        'products': products
    }
    return render(request, 'products/index.html', context)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})

def category_product_list(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = category.products.all()  # Related name from the Product model
    return render(request, 'products/product_list.html', {'category': category, 'products': products})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/products.html', {'products': products})

def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    gallery_media = GalleryMedia.objects.filter(product=product)
    colors = product.color if product.color else []
    sizes = product.size if product.size else []
    context = {
        'product': product,
        'gallery_media': gallery_media,
        'colors': colors,
        'sizes': sizes,
    }
    return render(request, 'products/product_detail.html', context)

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')

    for product_id, item in cart.items():
        if isinstance(item, dict):
            product = Product.objects.get(id=product_id)
            quantity = int(item['quantity'])  # Ensure quantity is an integer
            item_total = product.price * Decimal(quantity)
            total_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': item_total,
                'sizes': item['sizes'],
                'colors': item['colors']
            })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': sum(item['quantity'] for item in cart.values() if isinstance(item, dict))
    }
    return render(request, 'products/cart_detail.html', context)

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
            product_id_str = str(product.id)

            # Initialize list if product not in cart
            if product_id_str not in cart:
                cart[product_id_str] = []

            # Iterate over all size and color combinations
            for size in sizes:
                for color in colors:
                    # Check if this combination already exists in the cart
                    existing_item = next(
                        (item for item in cart[product_id_str] if item['size'] == size and item['color'] == color),
                        None
                    )
                    if existing_item:
                        existing_item['quantity'] += quantity
                    else:
                        cart[product_id_str].append({
                            'size': size,
                            'color': color,
                            'quantity': quantity
                        })

            request.session['cart'] = cart

            # Calculate total_price and cart_count
            total_price = sum(
                Product.objects.get(id=int(pid)).price * sum(item['quantity'] for item in items)
                for pid, items in cart.items()
            )
            cart_count = sum(
                item['quantity'] for items in cart.values() for item in items
            )

            return JsonResponse({
                'cart_count': cart_count,
                'total_price': float(total_price),
                'success': True,
                'message': 'Product added to cart successfully.'
            })
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
    size = request.GET.get('size')
    color = request.GET.get('color')
    quantity = int(request.GET.get('quantity', 1))
    cart = request.session.get('cart', {})
    product_id_str = str(product.id)
    
    if product_id_str in cart:
        # Find the specific combination
        for item in cart[product_id_str]:
            if item['size'] == size and item['color'] == color:
                item['quantity'] = quantity
                break
        else:
            # If combination doesn't exist, add it
            cart[product_id_str].append({
                'size': size,
                'color': color,
                'quantity': quantity
            })
    else:
        # Add new product with the combination
        cart[product_id_str] = [{
            'size': size,
            'color': color,
            'quantity': quantity
        }]
    
    request.session['cart'] = cart
    
    # Calculate total_price
    total_price = sum(
        Product.objects.get(id=int(pid)).price * sum(item['quantity'] for item in items)
        for pid, items in cart.items()
    )
    
    cart_count = sum(
        item['quantity'] for items in cart.values() for item in items
    )
    
    return JsonResponse({
        'cart_count': cart_count,
        'total_price': float(total_price),
        'success': True,
        'message': 'Cart updated successfully.'
    })

def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                # Handle user registration or login
                if form.cleaned_data['create_account'] and not request.user.is_authenticated:
                    user = User.objects.create_user(
                        username=form.cleaned_data['email'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name']
                    )
                    user.save()
                    login(request, user)
                elif not request.user.is_authenticated:
                    user = None
                else:
                    user = request.user

                # Create order
                order = Order.objects.create(
                    user=user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    state=form.cleaned_data['state'],
                    zip_code=form.cleaned_data['zip_code'],
                    note=form.cleaned_data['note'],
                    payment_method=form.cleaned_data['payment_method']
                )

                # Create order items
                cart = request.session.get('cart', {})
                total_amount = Decimal('0.00')
                for product_id, items in cart.items():
                    product = Product.objects.get(id=int(product_id))
                    for item in items:
                        quantity = item['quantity']
                        size = item['size']
                        color = item['color']
                        item_total = product.price * Decimal(quantity)
                        total_amount += item_total
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price,
                            size=size,
                            color=color
                        )

                # Handle payment method
                if form.cleaned_data['payment_method'] == 'paystack':
                    response = paystack.transaction.initialize(
                        reference=f'order_{order.id}',
                        amount=int(total_amount * 100),  # Convert to kobo
                        email=order.email,
                        callback_url=request.build_absolute_uri(reverse('payment_callback'))
                    )
                    
                    if response['status']:
                        # Save transaction reference
                        order.transaction_reference = response['data']['reference']
                        order.save()
                        
                        # Redirect to Paystack payment page
                        return redirect(response['data']['authorization_url'])
                    else:
                        messages.error(request, 'Payment initialization failed')
                        return render(request, 'products/checkout.html', {'form': form})
                else:
                    # Pay on delivery
                    order.payment_status = 'Pending'
                    order.save()
                    
                    # Clear cart
                    request.session['cart'] = {}
                    
                    # Send confirmation email
                    send_order_confirmation_email(order)
                    
                    messages.success(request, 'Order placed successfully!')
                    return redirect('order_confirmation', order_id=order.id)

            except Exception as e:
                messages.error(request, f'Error processing your order: {str(e)}')
                return render(request, 'products/checkout.html', {'form': form})
        else:
            messages.error(request, 'Please check your input.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = CheckoutForm(initial=initial_data, user=request.user)
    
    return render(request, 'products/checkout.html', {'form': form})

@csrf_exempt
def paystack_webhook(request):
    payload = json.loads(request.body)
    event = payload.get('event')
    
    if event == 'charge.success':
        data = payload.get('data', {})
        reference = data.get('reference')
        
        try:
            order = Order.objects.get(transaction_reference=reference)
            order.payment_status = 'Paid'
            order.save()
            
            # Clear cart and send confirmation
            request.session['cart'] = {}
            send_order_confirmation_email(order)
            
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'})
            
    return JsonResponse({'status': 'success'})

def payment_callback(request):
    reference = request.GET.get('reference')
    if reference:
        try:
            order = Order.objects.get(transaction_reference=reference)
            # Verify payment status
            response = paystack.transaction.verify(reference)
            if response['status'] and response['data']['status'] == 'success':
                order.payment_status = 'Paid'
                order.save()
                
                # Clear cart
                request.session['cart'] = {}
                
                # Send confirmation email
                send_order_confirmation_email(order)
                
                messages.success(request, 'Payment successful!')
            else:
                messages.error(request, 'Payment verification failed')
            return redirect('order_confirmation', order_id=order.id)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
            return redirect('checkout')
    return redirect('checkout')

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    total_price = order_items.aggregate(total=Sum('price'))['total']
    return render(request, 'products/order_confirmation.html', {'order': order, 'order_items': order_items, 'total_price': total_price})

def send_order_confirmation_email(order):
    subject = 'Order Confirmation'
    
    message = render_to_string('products/order_confirmation_email.html', {'order': order})
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])
        logger.info(f'Order confirmation email sent to {order.email}')
    except Exception as e:
        logger.error(f'Error sending order confirmation email: {str(e)}')

def get_cart_sidebar_content(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')

    for product_id, item in cart.items():
        if isinstance(item, dict):
            product = Product.objects.get(id=product_id)
            quantity = int(item['quantity'])  # Ensure quantity is an integer
            item_total = product.price * Decimal(quantity)
            total_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': item_total,
                'sizes': item['sizes'],
                'colors': item['colors']
            })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': sum(item['quantity'] for item in cart.values() if isinstance(item, dict))
    }
    return render(request, 'products/sub_cart.html', context)


def order_list(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        orders = Order.objects.filter(session_key=session_key).order_by('-created_at')
    return render(request, 'products/order_list.html', {'orders': orders})

from django.db.models import Sum, F


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    total_price = order_items.aggregate(total=Sum(F('price') * F('quantity')))['total']
    
    # Calculate total price for each item
    for item in order_items:
        item.total_price = item.price * item.quantity
    
    return render(request, 'products/order_detail.html', {'order': order, 'order_items': order_items, 'total_price': total_price})