# Generated by Django 3.2.24 on 2024-09-30 01:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0106_alter_invitation_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('email',), 'permissions': (('manage_users', 'Manage customers.'), ('manage_staff', 'Manage staff.'), ('impersonate_user', 'Impersonate user.'), ('read_users', 'Read user info only.'))},
        ),
    ]
