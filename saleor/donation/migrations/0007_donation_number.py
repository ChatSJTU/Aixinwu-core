# Generated by Django 3.2.24 on 2024-07-17 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0006_alter_donation_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='number',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]
