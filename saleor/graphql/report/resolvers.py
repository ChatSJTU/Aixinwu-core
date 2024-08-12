from django.db.models import Q, Sum

from saleor.account import CustomerEvents
from saleor.donation import DonationStatus

from ...account.models import CustomerEvent
from ...donation.models import Donation
from ...order import OrderStatus
from ...order.models import Order
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.types.common import DateTimeRangeInput
from ..utils.filters import filter_range_field
from .types import BaseReport


def resolve_order_report(info: ResolveInfo, date: DateTimeRangeInput):
    qs = Order.objects.using(get_database_connection_name(info.context))
    qs = filter_range_field(qs, "created_at", date)
    qs = qs.exclude(
        Q(status=OrderStatus.CANCELED)
        | Q(status=OrderStatus.UNCONFIRMED)
        | Q(status=OrderStatus.EXPIRED)
    ).annotate(quantity_ordered=Sum("lines__quantity"))
    collectionTotal = qs.count()
    agg = qs.aggregate(
        quantitiesTotal=Sum("quantity_ordered"), amountTotal=Sum("total_net_amount")
    )
    return BaseReport(
        collectionTotal=collectionTotal,
        quantitiesTotal=agg["quantitiesTotal"],
        amountTotal=agg["amountTotal"],
    )


def resolve_customers_registered(info: ResolveInfo, date: DateTimeRangeInput):
    qs = CustomerEvent.objects.using(get_database_connection_name(info.context))
    qs = filter_range_field(qs, "date", date)
    qs = qs.filter(type=CustomerEvents.ACCOUNT_CREATED)
    return qs.count()


def resolve_donation_report(info: ResolveInfo, date: DateTimeRangeInput):
    qs = Donation.objects.using(get_database_connection_name(info.context))
    qs = filter_range_field(qs, "created_at", date)
    qs = qs.filter(status=DonationStatus.COMPLETED)
    collectionTotal = qs.count()
    agg = qs.aggregate(quantitiesTotal=Sum("quantity"), amountTotal=Sum("price_amount"))
    return BaseReport(
        collectionTotal=collectionTotal,
        quantitiesTotal=agg["quantitiesTotal"],
        amountTotal=agg["amountTotal"],
    )
