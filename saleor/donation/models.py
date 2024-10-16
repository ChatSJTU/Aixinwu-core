import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_prices.models import MoneyField

from saleor import settings

from ..permission.enums import DonationPermissions
from . import DonationStatus


def get_donation_number():
    now = timezone.now()
    current_year_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    return Donation.objects.filter(created_at__gte=current_year_month).count() + 1


class Donation(models.Model):
    id = models.UUIDField(
        primary_key=True, editable=False, unique=True, default=uuid.uuid4
    )
    number = models.IntegerField(default=get_donation_number, null=True, blank=True)
    donator = models.CharField(max_length=128, null=True, blank=True)
    barcode = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        null=True,
        blank=True,
    )
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=32,
        default=DonationStatus.UNREVIEWED,
        choices=DonationStatus.CHOICES,
        null=True,
        blank=True,
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("-created_at", "pk")
        permissions = (
            (DonationPermissions.MANAGE_DONATIONS.codename, "Manage donations"),
            (DonationPermissions.ADD_DONATIONS.codename, "Add donations"),
        )
