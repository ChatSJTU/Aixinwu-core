from django.db import models
from saleor import settings
from django_prices.models import MoneyField
from django.conf import settings
from saleor.account.models import User
from saleor.permission.enums import DonationPermissions
import uuid


class Donation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    donator = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("-created_at", "pk")
        permissions = (
            (DonationPermissions.MANAGE_DONATIONS.codename, "Manage donations"),
        )
