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
    path('cart/update-cart-item/<slug:product_slug>/', views.update_cart_item, name='update_cart_item'),  # Updated path
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
]
