# Generated by Django 3.2.24 on 2024-09-10 07:28

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0098_alter_user_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='balance',
            field=models.DecimalField(blank=True, decimal_places=3, default=Decimal('0.5'), max_digits=12),
        ),
    ]
