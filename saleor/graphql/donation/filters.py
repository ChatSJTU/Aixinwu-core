import django_filters
from django.db.models import Q

from ...donation.models import Donation
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.filters import (
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types.common import DateRangeInput
from ..core.types.filter_input import FilterInputObjectType
from ..utils.filters import filter_range_field


def filter_user(qs, _, value):
    qs = qs.filter(code=value)
    return qs


def filter_created_at_range(qs, _, value):
    return filter_range_field(qs, "created_at__date", value)


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at__date", value)


class DonationFilter(MetadataFilterBase):
    donator = django_filters.CharFilter(method=filter_user)
    created = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_created_at_range
    )
    updated = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_updated_at_range
    )

    class Meta:
        model = Donation
        fields = ["donator", "created", "updated"]


class DonationFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = DonationFilter
