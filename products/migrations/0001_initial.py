# Generated by Django 5.1.2 on 2024-11-26 13:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stock', models.PositiveIntegerField()),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('brand', models.CharField(blank=True, max_length=255)),
                ('tags', models.CharField(blank=True, max_length=255)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('dimensions', models.CharField(blank=True, max_length=255)),
                ('size', models.CharField(blank=True, max_length=50)),
                ('color', models.CharField(blank=True, max_length=50)),
                ('material', models.CharField(blank=True, max_length=255)),
                ('gender', models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('U', 'Unisex')], max_length=50)),
                ('promo_badge', models.BooleanField(default=False)),
                ('promo_badge_text', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_picture', models.ImageField(upload_to='media/product/%Y/%m/%d/')),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.category')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='GalleryMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video')], default='image', max_length=10)),
                ('image_1', models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/')),
                ('image_2', models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/')),
                ('image_3', models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/')),
                ('image_4', models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/')),
                ('video', models.FileField(blank=True, null=True, upload_to='media/product_gallery/videos/%Y/%m/%d/')),
                ('alt_text', models.CharField(blank=True, max_length=255)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_media', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Gallery',
                'verbose_name_plural': 'Product Gallery',
            },
        ),
    ]
