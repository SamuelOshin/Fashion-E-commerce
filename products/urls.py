from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:category_slug>/', views.category_list, name='product_list'),
    path('shop/', views.product_list, name='shop'),
    path('products/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<slug:product_slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<slug:product_slug>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update-cart-item/<slug:product_slug>/', views.update_cart_item, name='update_cart_item'),
    path('cart-sidebar-content/', views.get_cart_sidebar_content, name='cart_sidebar_content'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cart/clear/', views.clear_cart, name='clear-cart'),
    path('cart-count/', views.cart_count, name='cart_count'),

]
