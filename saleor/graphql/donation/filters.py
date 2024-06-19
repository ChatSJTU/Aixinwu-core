from ..utils.filters import filter_range_field
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types.filter_input import FilterInputObjectType
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types.common import DateRangeInput
from ...donation.models import Donation

from django.db.models import Q
import django_filters


def filter_user(qs, _, value):
    qs = qs.filter(
        Q(user__email__ilike=value)
        | Q(user__email__trigram_similar=value)
        | Q(user__first_name__trigram_similar=value)
        | Q(user__last_name__trigram_similar=value)
        | Q(user__code__trigram_similar=value)
        | Q(user__account__trigram_similar=value)
    )
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
