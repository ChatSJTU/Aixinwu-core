# Generated by Django 3.2.24 on 2024-06-19 03:29

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0087_alter_user_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerevent',
            name='balance',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='customerevent',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_events', to='account.user'),
        ),
        migrations.CreateModel(
            name='BalanceEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('type', models.CharField(choices=[('DONATION_GRANTED', 'donation_granted'), ('FIRST_LOGIN', 'first_login'), ('CONSUMED', 'consumed')], max_length=255)),
                ('balance', models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='balance_events', to='account.user')),
            ],
            options={
                'ordering': ('date',),
            },
        ),
    ]
