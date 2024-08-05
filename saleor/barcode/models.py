from django.db import models
from django.db.models import Max
from django.utils import timezone

from ..permission.enums import BarcodePermissions


def current_year_month():
    return int(timezone.now().strftime("%y%m"))


def get_sub():
    year_month = current_year_month()
    i = (
        Barcode.objects.filter(year_month=year_month)
        .all()
        .aggregate(Max("sub"))["sub__max"]
        or 0
    ) + 1
    return i


class Barcode(models.Model):
    id = models.AutoField(primary_key=True)
    year_month = models.IntegerField(
        editable=False, null=False, blank=False, default=current_year_month
    )
    used = models.BooleanField(default=False, editable=True, null=False, blank=False)
    sub = models.IntegerField(editable=False, null=False, blank=False, default=get_sub)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class Meta:
        ordering = ("-created_at",)
        permissions = ((BarcodePermissions.MANAGE_BARCODE.codename, "Manage barcodes"),)
