# Generated by Django 3.2.24 on 2024-06-18 14:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0043_alter_sitecarousel_deleted_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitecarousel',
            name='site',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='carousel', to='site.sitesettings'),
        ),
    ]
