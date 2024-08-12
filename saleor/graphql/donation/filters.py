from datetime import datetime

import django_filters

from ...donation.models import Donation
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.filters import (
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types.common import DateRangeInput
from ..core.types.filter_input import FilterInputObjectType
from ..utils.filters import filter_range_field


def filter_title(qs, _, value):
    return qs.filter(title__contains=value)


def filter_number(qs, _, value):
    try:
        dt = datetime.strptime("y%m", value[:4])
        sub = int(value[-4:0])
        return qs.filter(created_at__gte=dt).filter(number=sub)
    except ValueError:
        return qs.filter(title="INVALID")


def filter_user(qs, _, value):
    qs = qs.filter(donator=value)
    return qs


def filter_created_at_range(qs, _, value):
    return filter_range_field(qs, "created_at__date", value)


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at__date", value)


class DonationFilter(MetadataFilterBase):
    donator = django_filters.CharFilter(method=filter_user)
    title = django_filters.CharFilter(method=filter_title)
    number = django_filters.CharFilter(method=filter_number)
    created = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_created_at_range
    )
    updated = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_updated_at_range
    )

    class Meta:
        model = Donation
        fields = ["donator", "title", "number", "created", "updated"]


class DonationFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = DonationFilter
