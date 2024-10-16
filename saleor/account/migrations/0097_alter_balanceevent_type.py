# Generated by Django 3.2.24 on 2024-08-05 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0096_alter_balanceevent_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='balanceevent',
            name='type',
            field=models.CharField(choices=[('DONATION_GRANTED', 'donation_granted'), ('DONATION_REJECTED', 'donation_rejected'), ('FIRST_LOGIN', 'first_login'), ('MANUALLY_UPDATED', 'manually_updated'), ('CONSECUTIVE_LOGIN', 'consecutive_login'), ('CONSUMED', 'consumed'), ('REFUNDED', 'refunded')], max_length=255),
        ),
    ]
