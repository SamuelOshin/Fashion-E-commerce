# Generated by Django 5.1.2 on 2025-01-14 08:52

import pyuploadcare.dj.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_alter_product_color_alter_product_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='photo',
            field=pyuploadcare.dj.models.ImageField(blank=True),
        ),
    ]