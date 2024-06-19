# Generated by Django 3.2.24 on 2024-06-19 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0090_remove_user_continuous'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='consecutive_logins',
        ),
        migrations.AddField(
            model_name='user',
            name='continuous',
            field=models.IntegerField(blank=True, default=1),
        ),
    ]
