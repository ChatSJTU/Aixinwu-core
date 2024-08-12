from datetime import datetime

from django.db.models import Max, Min, Q, Sum
from django.forms import ValidationError

from ...account.models import CustomerEvent, CustomerEvents
from ...donation.models import Donation, DonationStatus
from ...order import OrderStatus
from ...order.models import Order
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.types.common import DateTimeRangeInput
from ..utils.filters import filter_range_field
from .types import BaseReport, Granularity, get_relative_delta


def _revise_date_input(qs, field, date: DateTimeRangeInput) -> DateTimeRangeInput:
    if not date.lte:
        date.lte = qs.aggregate(lte=Max(field))["lte"]
    if not date.gte:
        date.gte = qs.aggregate(gte=Min(field))["gte"]

    if date.lte is None or date.gte is None:
        raise ValidationError(message="Range not found.")

    return date


def _split_date_input(
    date: DateTimeRangeInput, granularity: Granularity
) -> list[dict[str, datetime]]:
    ranges: list[dict[str, datetime]] = []
    delta = get_relative_delta(granularity)
    x = date.gte
    y = date.lte
    while x + delta < y:
        ranges.append(dict(gte=x, lte=x + delta))
        x = x + delta
    ranges.append(dict(gte=x, lte=x + delta))
    return ranges


def resolve_order_reports(
    info: ResolveInfo, date: DateTimeRangeInput, granularity: Granularity
) -> list[BaseReport]:
    qs = Order.objects.using(get_database_connection_name(info.context)).exclude(
        Q(status=OrderStatus.CANCELED)
        | Q(status=OrderStatus.UNCONFIRMED)
        | Q(status=OrderStatus.EXPIRED)
    )
    try:
        date = _revise_date_input(qs, "created_at", date)
    except ValidationError:
        return list()

    results = []
    for dt in _split_date_input(date, granularity):
        qss = qs.all()
        qss = filter_range_field(qss, "created_at", dt)
        qss = qss.annotate(quantity_ordered=Sum("lines__quantity"))
        collectionTotal = qss.count()
        agg = qss.aggregate(
            quantitiesTotal=Sum("quantity_ordered"), amountTotal=Sum("total_net_amount")
        )
        results.append(
            BaseReport(
                collectionTotal=collectionTotal,
                quantitiesTotal=agg["quantitiesTotal"],
                amountTotal=agg["amountTotal"],
            )
        )
    return results


def resolve_customers_registered(
    info: ResolveInfo, date: DateTimeRangeInput, granularity: Granularity
) -> list[int]:
    qs = CustomerEvent.objects.using(get_database_connection_name(info.context)).filter(
        type=CustomerEvents.ACCOUNT_CREATED
    )
    try:
        date = _revise_date_input(qs, "date", date)
    except ValidationError:
        return list()

    results: list[int] = []

    for dt in _split_date_input(date, granularity):
        qss = qs.all()
        qss = filter_range_field(qss, "date", dt)
        results.append(qss.count())

    return results


def resolve_donation_reports(
    info: ResolveInfo, date: DateTimeRangeInput, granularity: Granularity
) -> list[BaseReport]:
    qs = Donation.objects.using(get_database_connection_name(info.context)).filter(
        status=DonationStatus.COMPLETED
    )

    try:
        date = _revise_date_input(qs, "created_at", date)
    except ValidationError:
        return list()

    results: list[BaseReport] = []
    for dt in _split_date_input(date, granularity):
        qss = qs.all()
        qss = filter_range_field(qss, "created_at", dt)
        collectionTotal = qss.count()
        agg = qss.aggregate(
            quantitiesTotal=Sum("quantity"), amountTotal=Sum("price_amount")
        )
        results.append(
            BaseReport(
                collectionTotal=collectionTotal,
                quantitiesTotal=agg["quantitiesTotal"],
                amountTotal=agg["amountTotal"],
            )
        )
    return results
