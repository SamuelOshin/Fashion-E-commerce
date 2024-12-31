from decimal import Decimal
from .models import Product
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Order, OrderItem
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string  # Add this import
import logging

logger = logging.getLogger(__name__)

def cart_details(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
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
                # Ensure 'quantity' exists and is an integer
                quantity = int(item.get('quantity', 1))
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting quantity for product '{product_id}': {e}")
                quantity = 1  # Fallback to default quantity

            # Calculate total price for this item
            try:
                price = float(item.get('price', 0))
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting price for product '{product_id}': {e}")
                price = 0.0

            item_total = price * quantity
            total_price += item_total
            cart_count += quantity

            # Fetch the Product instance
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                logger.error(f"Product with id '{product_id}' does not exist.")
                product = None

            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': f"{item_total:.2f}",
                'size': item.get('size', 'N/A'),
                'color': item.get('color', 'N/A')
            })

    context = {
        'cart_items': cart_items,
        'total_price': f"{total_price:.2f}",
        'cart_count': cart_count
    }

    return context  # Return context for templates
