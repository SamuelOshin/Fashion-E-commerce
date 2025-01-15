from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from datetime import datetime
from django.contrib.auth.models import User
from multiselectfield import MultiSelectField
from decimal import Decimal
from pyuploadcare.dj.models import ImageField

SIZE_CHOICES = [
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('2XL', 'Extra Extra Large'),
    ('6', 'Size 6'),
    ('7', 'Size 7'),
    ('8', 'Size 8'),
    ('9', 'Size 9'),
    ('10', 'Size 10'),
    ('11', 'Size 11'),
    ('12', 'Size 12'),
]

COLOR_CHOICES = [
    ('#000000', 'Black'),
    ('#FFFFFF', 'White'),
    ('#FF0000', 'Red'),
    ('#00FF00', 'Green'),
    ('#0000FF', 'Blue'),
    ('#FFFF00', 'Yellow'),
    ('#FFA500', 'Orange'),
    ('#800080', 'Purple'),
    ('#FFC0CB', 'Pink'),
    ('#A52A2A', 'Brown'),
    ('#808080', 'Gray'),
    ('#00FFFF', 'Cyan'),
    ('#008000', 'Dark Green'),
    ('#FFD700', 'Gold'),
    ('#4B0082', 'Indigo'),
    ('#ADD8E6', 'Light Blue'),
    ('#800000', 'Maroon'),
    ('#000080', 'Navy'),
    ('#808000', 'Olive'),
    ('#FF4500', 'Orange Red'),
    ('#DA70D6', 'Orchid'),
    ('#EEE8AA', 'Pale Goldenrod'),
    ('#98FB98', 'Pale Green'),
    ('#AFEEEE', 'Pale Turquoise'),
    ('#DB7093', 'Pale Violet Red'),
    ('#FFEFD5', 'Papaya Whip'),
    ('#FFDAB9', 'Peach Puff'),
    ('#CD853F', 'Peru'),
    ('#FFC0CB', 'Pink'),
    ('#DDA0DD', 'Plum'),
    ('#B0E0E6', 'Powder Blue'),
    ('#BC8F8F', 'Rosy Brown'),
    ('#4169E1', 'Royal Blue'),
    ('#8B4513', 'Saddle Brown'),
    ('#FA8072', 'Salmon'),
    ('#F4A460', 'Sandy Brown'),
    ('#2E8B57', 'Sea Green'),
    ('#FFF5EE', 'Sea Shell'),
    ('#A0522D', 'Sienna'),
    ('#C0C0C0', 'Silver'),
    ('#87CEEB', 'Sky Blue'),
    ('#6A5ACD', 'Slate Blue'),
    ('#708090', 'Slate Gray'),
    ('#FFFAFA', 'Snow'),
    ('#00FF7F', 'Spring Green'),
    ('#4682B4', 'Steel Blue'),
    ('#D2B48C', 'Tan'),
    ('#008080', 'Teal'),
    ('#D8BFD8', 'Thistle'),
    ('#FF6347', 'Tomato'),
    ('#40E0D0', 'Turquoise'),
    ('#EE82EE', 'Violet'),
    ('#F5DEB3', 'Wheat'),
    ('#F5F5F5', 'White Smoke'),
    ('#9ACD32', 'Yellow Green'),
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('U', 'Unisex'),
]

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    stock = models.PositiveIntegerField()
    sku = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=255, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=255, blank=True)
    size = MultiSelectField(choices=SIZE_CHOICES, blank=True)
    color = MultiSelectField(choices=COLOR_CHOICES, blank=True)
    material = models.CharField(max_length=255, blank=True)
    gender = MultiSelectField(choices=GENDER_CHOICES, blank=True)
    promo_badge = models.BooleanField(default=False)
    promo_badge_text = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    product_picture = models.ImageField(upload_to='product/%Y/%m%d', blank=True)
    photo = ImageField(blank=True, manual_crop="")
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Check if the photo field has changed
        if self.pk:
            original = Product.objects.get(pk=self.pk)
            if original.photo != self.photo and not self.photo:
                self.photo = original.photo

        super(Product, self).save(*args, **kwargs)
        
    def __str__(self):
        return self.name

class GalleryMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_media')
    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPE_CHOICES, default='image'
    )
    image_1 = models.ImageField(upload_to='media/product_gallery/images/%Y/%m/%d/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='media/product_gallery/images/%Y/%m/%d/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='media/product_gallery/images/%Y/%m/%d/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='media/product_gallery/images/%Y/%m/%d/', blank=True, null=True)
    video = models.FileField(upload_to='media/product_gallery/videos/%Y/%m/%d/', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Gallery for {self.product.name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not (self.image_1 or self.image_2 or self.image_3 or self.image_4 or self.video):
            raise ValidationError("At least one image or video is required.")

    class Meta:
        verbose_name = "Product Gallery"
        verbose_name_plural = "Product Gallery"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.product.price

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    note = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='Pending')
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Order {self.id} by {self.first_name} {self.last_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, blank=True)  # Store color as hex code
    size = models.CharField(max_length=2, blank=True)  # Store size as a string

    def __str__(self):
        return f'OrderItem {self.id}'

def pre_save_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


pre_save.connect(pre_save_slug, sender=Category)
pre_save.connect(pre_save_slug, sender=Product)
