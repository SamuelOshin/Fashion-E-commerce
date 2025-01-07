import logging
import json
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
from django.contrib import messages
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.db.models import Sum, F
from django.utils import timezone
import requests
import uuid
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

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

    for product_id, items in cart.items():
        if isinstance(items, list):
            for item in items:
                try:
                    product = Product.objects.get(id=product_id)
                    quantity = int(item['quantity'])  # Ensure quantity is an integer
                    item_total = product.price * Decimal(quantity)
                    total_price += item_total
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'total_price': item_total,
                        'size': item.get('size', 'N/A'),
                        'color': item.get('color', 'N/A')
                    })
                except Product.DoesNotExist:
                    logger.error(f"Product with id '{product_id}' does not exist.")
                    continue

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': sum(item['quantity'] for items in cart.values() for item in items if isinstance(item, dict))
    }
    return render(request, 'products/cart_detail.html', context)

@csrf_exempt
@require_POST
def add_to_cart(request, product_slug):
    logger.debug(f'Received body: {request.body}')
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error('Invalid JSON data.')
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)

    size = data.get('size')
    color = data.get('color')
    quantity = data.get('quantity', 1)

    if not size or not color:
        logger.error('Missing size or color.')
        return JsonResponse({'success': False, 'message': 'Please select at least one size and one color.'}, status=400)

    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1  # Fallback to default quantity

    product = get_object_or_404(Product, slug=product_slug)

    # Initialize the cart in session if not present
    cart = request.session.get('cart', {})

    product_id = str(product.id)
    if product_id in cart:
        # Ensure cart[product_id] is a list of dictionaries
        if not isinstance(cart[product_id], list):
            cart[product_id] = []

        # Check for same size and color
        for item in cart[product_id]:
            if isinstance(item, dict) and item.get('size') == size and item.get('color') == color:
                # Update the quantity
                item['quantity'] = int(item.get('quantity', 1)) + quantity
                break
        else:
            # Add new item with different size/color
            cart[product_id].append({
                'name': product.name,
                'price': str(product.price),
                'image_url': product.product_picture.url if product.product_picture else '',
                'size': size,
                'color': color,
                'quantity': quantity,
                'slug': product.slug
            })
    else:
        # Add new product with size and color as list
        cart[product_id] = [{
            'name': product.name,
            'price': str(product.price),
            'image_url': product.product_picture.url if product.product_picture else '',
            'size': size,
            'color': color,
            'quantity': quantity,
            'slug': product.slug
        }]

    # Save the updated cart back to the session
    request.session['cart'] = cart
    request.session.modified = True

    # Calculate cart count
    cart_count = sum(
        item['quantity'] for items in cart.values() for item in items if isinstance(item, dict)
    )

    return JsonResponse({
        'success': True,
        'message': 'Product added to cart successfully.',
        'cart_count': cart_count
    })

@csrf_exempt
@require_POST
def remove_from_cart(request, product_slug):
    """
    Remove a specific item from the cart based on product_slug, size, and color.
    Expects a JSON payload with 'size' and 'color'.
    """
    try:
        data = json.loads(request.body)
        size = data.get('size')
        color = data.get('color')

        if not size or not color:
            return JsonResponse({'success': False, 'message': 'Missing size or color information.'}, status=400)

        product = get_object_or_404(Product, slug=product_slug)
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)

        if product_id_str in cart:
            # Filter out the item matching size and color
            original_length = len(cart[product_id_str])
            cart[product_id_str] = [
                item for item in cart[product_id_str]
                if not (item.get('size') == size and item.get('color') == color)
            ]

            if len(cart[product_id_str]) < original_length:
                # Update the session cart
                request.session['cart'] = cart
                cart_count = sum(
                    item['quantity'] for items in cart.values() for item in items if isinstance(item, dict)
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Item removed from cart.',
                    'cart_count': cart_count
                })
            else:
                return JsonResponse({'success': False, 'message': 'Item not found in cart.'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': 'Product not found in cart.'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f'Error removing from cart: {str(e)}')
        return JsonResponse({'success': False, 'message': 'An error occurred while removing the item.'}, status=500)

@require_POST
def update_cart_item(request, product_slug):
    try:
        data = json.loads(request.body)
        product = get_object_or_404(Product, slug=product_slug)
        
        size = data.get('size')
        color = data.get('color')
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            quantity = 1
            
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        # Ensure cart has list structure
        if product_id_str not in cart:
            cart[product_id_str] = []
        
        # Find and update matching variation
        updated = False
        for item in cart[product_id_str]:
            if item.get('size') == size and item.get('color') == color:
                item['quantity'] = quantity
                updated = True
                break
                
        if not updated:
            # Add as new variation if not found
            cart[product_id_str].append({
                'name': product.name,
                'price': str(product.price),
                'image_url': product.product_picture.url if product.product_picture else '',
                'size': size,
                'color': color, 
                'quantity': quantity,
                'slug': product.slug
            })
        
        request.session['cart'] = cart
        request.session.modified = True
        
        # Calculate item total
        item_total = float(product.price) * quantity
        
        # Calculate overall cart total price
        total_price = Decimal('0.00')
        for pid, items in cart.items():
            for itm in items:
                total_price += Decimal(itm['price']) * itm['quantity']
        
        # Calculate cart count
        cart_count = sum(
            item['quantity'] for items in cart.values() for item in items if isinstance(item, dict)
        )
        
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'total_price': float(total_price),
            'item_total': item_total,
            'message': 'Cart updated successfully.'
        })
        
    except (json.JSONDecodeError, ValueError, TypeError, Product.DoesNotExist) as e:
        logger.error(f"Error updating cart item: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to update cart item.'
        }, status=400)


def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            create_account = form.cleaned_data.get('create_account')

            if create_account and not request.user.is_authenticated:
                try:
                    # Create a new user
                    user = User.objects.create_user(
                        username=form.cleaned_data.get('email'),  # Using email as username for uniqueness
                        email=form.cleaned_data.get('email'),
                        password=form.cleaned_data.get('password1'),
                        first_name=form.cleaned_data.get('first_name'),
                        last_name=form.cleaned_data.get('last_name'),
                    )

                    # Authenticate the user
                    user = authenticate(
                        request,
                        username=form.cleaned_data.get('email'),
                        password=form.cleaned_data.get('password1')
                    )

                    if user is not None:
                        # Automatically sign in the user
                        login(request, user)
                        messages.success(request, 'Account created and signed in successfully.')
                    else:
                        messages.error(request, 'Authentication failed. Please try logging in manually.')
                        return render(request, 'products/checkout.html', {'form': form})

                except Exception as e:
                    logger.error(f"Error creating user: {str(e)}")
                    messages.error(request, 'Account creation failed. Please try again.')
                    return render(request, 'products/checkout.html', {'form': form})

            try:
                # Collect form data
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                email = form.cleaned_data.get('email')
                address = form.cleaned_data.get('address')
                city = form.cleaned_data.get('city')
                state = form.cleaned_data.get('state')
                zip_code = form.cleaned_data.get('zip_code')
                note = form.cleaned_data.get('note')
                payment_method = form.cleaned_data.get('payment_method')
                
                # Get or create session key for guest users
                if not request.user.is_authenticated:
                    if not request.session.session_key:
                        request.session.create()
                    session_key = request.session.session_key
                else:
                    session_key = None  # Not needed for authenticated users
                
                # Create Order without total_price
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=session_key,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    note=note,
                    payment_method=payment_method,
                    payment_status='Pending',
                    created_at=timezone.now()
                )
                
                # Populate OrderItems from Cart and calculate total_price
                cart = request.session.get('cart', {})
                total = Decimal('0.00')
                for product_id, items in cart.items():
                    product = get_object_or_404(Product, id=product_id)
                    for item in items:
                        size = item.get('size')
                        color = item.get('color')
                        quantity = item.get('quantity', 1)
                        price = Decimal(item.get('price', '0.00'))
                        
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            size=size,
                            color=color,
                            quantity=quantity,
                            price=price
                        )
                        total += price * quantity

                # Update order's total_price
                order.total_price = total
                order.save()
                
                # Clear the cart after successful order creation
                request.session['cart'] = {}
                request.session.modified = True
                
                # Optionally, send confirmation email
                send_order_confirmation_email(order)
                
                if payment_method == 'paystack':
                    # Initialize Paystack Payment
                    reference = str(uuid.uuid4())
                    amount = int(order.total_price * 100)  # Paystack expects amount in kobo
                    callback_url = request.build_absolute_uri('/products/payment/callback/')
                    
                    payload = {
                        'email': email,
                        'amount': amount,
                        'reference': reference,
                        'callback_url': callback_url,
                        'metadata': {
                            'order_id': order.id
                        }
                    }
                    
                    headers = {
                        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                        'Content-Type': 'application/json',
                    }
                    
                    try:
                        response = requests.post('https://api.paystack.co/transaction/initialize', json=payload, headers=headers)
                        response_data = response.json()
                        
                        if response_data.get('status'):
                            authorization_url = response_data['data']['authorization_url']
                            # Save Paystack reference to order
                            order.paystack_reference = reference
                            order.save()
                            return redirect(authorization_url)
                        else:
                            logger.error(f"Paystack Initialization Failed: {response_data.get('message')}")
                            messages.error(request, 'Payment initialization failed. Please try again.')
                            return redirect('checkout')
                    except Exception as e:
                        logger.exception("Exception during Paystack initialization.")
                        messages.error(request, 'An unexpected error occurred during payment processing.')
                        return redirect('checkout')
                
                # If not Paystack, proceed to order confirmation
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('order_confirmation', order_id=order.id)
                
            except Exception as e:
                logger.error(f"Checkout error: {str(e)}")
                messages.error(request, 'There was an error processing your order. Please try again.')
                return render(request, 'products/checkout.html', {'form': form})
        else:
            # Handle GET request
            initial_data = {}
            if request.user.is_authenticated:
                initial_data = {
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'email': request.user.email,
                }
            form = CheckoutForm(initial=initial_data, user=request.user)
            return render(request, 'products/checkout.html', {'form': form})
    else:
        # Handle GET request
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
            # Retrieve the order using paystack_reference
            order = Order.objects.get(paystack_reference=reference)
            order.payment_status = 'Paid'
            order.save()
            
            # Clear cart and send confirmation
            request.session['cart'] = {}
            send_order_confirmation_email(order)
            
        except Order.DoesNotExist:
            logger.error(f"Order with paystack_reference {reference} not found.")
            return JsonResponse({'status': 'error', 'message': 'Order not found'})
            
    return JsonResponse({'status': 'success'})

@csrf_exempt
def payment_callback(request):
    reference = request.GET.get('reference')
    if reference:
        try:
            # Retrieve the order using paystack_reference
            order = Order.objects.get(paystack_reference=reference)
            
            # Verify payment status with Paystack
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
    messages.success(request, 'Your order has been placed successfully!')
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
    cart_count = 0

    for product_id, items in cart.items():
        if not isinstance(items, list):
            logger.error(f"Invalid cart item format for '{product_id}': Expected list, got {type(items).__name__}")
            continue  # Skip items with unexpected structure

        for item in items:
            if not isinstance(item, dict):
                logger.error(f"Invalid cart item format for '{product_id}': Expected dict, got {type(item).__name__}")
                continue  # Skip invalid cart items

            try:
                product = Product.objects.get(id=product_id)
                quantity = int(item.get('quantity', 1))
                price = Decimal(item.get('price', '0.00'))
            except Product.DoesNotExist:
                logger.error(f"Product with id '{product_id}' does not exist.")
                continue
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing cart item for product '{product_id}': {e}")
                continue

            item_total = price * quantity
            total_price += item_total
            cart_count += quantity

            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': item_total,
                'size': item.get('size', 'N/A'),
                'color': item.get('color', 'N/A')
            })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count
    }

    # Render the 'sub_cart.html' template with the context
    rendered_html = render_to_string('products/sub_cart.html', context, request=request)
    return JsonResponse({'html': rendered_html, 'cart_count': cart_count}, status=200)


def order_list(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).annotate(
            calculated_total_price=Sum(F('items__price') * F('items__quantity'))
        ).order_by('-created_at')
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        orders = Order.objects.filter(session_key=session_key).annotate(
            calculated_total_price=Sum(F('items__price') * F('items__quantity'))
        ).order_by('-created_at')
    
    return render(request, 'products/order_list.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    total_price = order_items.aggregate(total=Sum(F('price') * F('quantity')))['total']
    
    # Calculate total price for each item
    for item in order_items:
        item.total_price = item.price * item.quantity
    
    return render(request, 'products/order_detail.html', {'order': order, 'order_items': order_items, 'total_price': total_price})

def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    return redirect('shop')