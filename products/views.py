from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, GalleryMedia, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CheckoutForm, LoginForm
from .models import Order, OrderItem, Product
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

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
    gallery_media = product.gallery_media.all()
    colors = product.color.split(',') if product.color else []
    return render(request, 'products/product_detail.html', {
        'product': product,
        'gallery_media': gallery_media,
        'colors': colors,
        'stock': product.stock
    })

def cart_detail(request):
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
    return render(request, 'products/cart_detail.html', {'cart_items': cart_items, 'total_price': total_price})

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

def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Handle user registration or login
            if form.cleaned_data['create_account']:
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                login(request, user)
            else:
                user = authenticate(
                    request,
                    username=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                if user is not None:
                    login(request, user)
                else:
                    return render(request, 'checkout.html', {'form': form, 'error': 'Invalid login credentials'})

            # Process the order
            order = Order.objects.create(
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
            cart = request.session.get('cart', {})
            for product_id, quantity in cart.items():
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
            # Clear the cart
            request.session['cart'] = {}

            # Send order confirmation email
            subject = 'Order Confirmation'
            message = render_to_string('order_confirmation_email.html', {'order': order})
            send_mail(subject, message, settings.EMAIL_HOST_USER, [order.email], fail_silently=False)

            return redirect('order_confirmation', order_id=order.id)
    else:
        form = CheckoutForm()
    return render(request, 'checkout.html', {'form': form})