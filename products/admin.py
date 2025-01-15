from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Category, Product, GalleryMedia, Order, OrderItem
from django.contrib.admin import site
from django.shortcuts import render
from products.models import Order
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django import forms
from django.utils.translation import gettext_lazy as _

# Unregister the default User and Group admin classes
admin.site.unregister(User)
admin.site.unregister(Group)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def has_add_permission(self, request):
        return False  # Disable adding orders from the admin interface

    def has_delete_permission(self, request, obj=None):
        return False  # Disable deleting orders from the admin interface

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'size': forms.CheckboxSelectMultiple,
            'color': forms.CheckboxSelectMultiple,
            'gender': forms.CheckboxSelectMultiple,
        }

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'price', 'stock', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name', 'sku', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


class MyAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        # Calculate the data
        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()

        # Add your data to the context
        extra_context = extra_context or {}
        extra_context.update({
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
        })
        
        return super().index(request, extra_context=extra_context)

# Register your custom admin site
admin_site = MyAdminSite(name='my_admin')

# Register the User model with the custom UserAdmin class
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

# Register the Group model with the custom GroupAdmin class
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass