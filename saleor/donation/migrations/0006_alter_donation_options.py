# Generated by Django 3.2.24 on 2024-07-17 02:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0005_auto_20240714_0620'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='donation',
            options={'ordering': ('-created_at', 'pk'), 'permissions': (('manage_donations', 'Manage donations'), ('add_donations', 'Add donations'))},
        ),
    ]
