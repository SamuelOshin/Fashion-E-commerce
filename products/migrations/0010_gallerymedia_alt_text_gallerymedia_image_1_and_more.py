# Generated by Django 5.1.2 on 2025-01-14 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_remove_gallerymedia_alt_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gallerymedia',
            name='alt_text',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='gallerymedia',
            name='image_1',
            field=models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='gallerymedia',
            name='image_2',
            field=models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='gallerymedia',
            name='image_3',
            field=models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='gallerymedia',
            name='image_4',
            field=models.ImageField(blank=True, null=True, upload_to='media/product_gallery/images/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='gallerymedia',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='media/product_gallery/videos/%Y/%m/%d/'),
        ),
    ]
