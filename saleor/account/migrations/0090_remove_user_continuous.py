# Generated by Django 3.2.24 on 2024-06-19 07:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0089_auto_20240619_0734'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='continuous',
        ),
    ]
