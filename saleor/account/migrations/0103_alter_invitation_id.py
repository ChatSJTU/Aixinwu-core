# Generated by Django 3.2.24 on 2024-09-27 15:46

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0102_auto_20240927_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
