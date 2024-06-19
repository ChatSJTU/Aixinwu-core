from saleor.graphql.utils.filters import filter_range_field
from ..account.enums import BalanceEventsEnum
from ...account.models import BalanceEvent
from ..core.doc_category import DOC_CATEGORY_EVENTS
from ..core.types.filter_input import FilterInputObjectType
from ..core.filters import (
    EnumFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types.common import DateRangeInput
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


def filter_account(qs, _, value):
    return qs.filter(user__account=value)


def filter_date_range(qs, _, value):
    return filter_range_field(qs, "date__date", value)


def filter_type(qs, _, value):
    return qs.filter(type=value)


class BalanceEventFilter(MetadataFilterBase):
    user = django_filters.CharFilter(method=filter_user)
    type = EnumFilter(input_class=BalanceEventsEnum, method=filter_type)
    date = ObjectTypeFilter(input_class=DateRangeInput, method=filter_date_range)

    class Meta:
        model = BalanceEvent
        fields = ["user", "date", "type"]


class BalanceEventFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        filterset_class = BalanceEventFilter
