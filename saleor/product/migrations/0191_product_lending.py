# Generated by Django 3.2.24 on 2024-06-19 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0190_merge_20231221_1337'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='lending',
            field=models.BooleanField(default=False),
        ),
    ]
