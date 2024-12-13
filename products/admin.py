from django.contrib import admin
from .models import Category, Product, GalleryMedia, Order, OrderItem

admin.site.register(Category)
admin.site.register(GalleryMedia)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
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

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name', 'sku', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Product, ProductAdmin)