from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.types.filter_input import FilterInputObjectType
from ..core.filters import GlobalIDMultipleChoiceFilter, MetadataFilterBase, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ...donation.models import Donation
import django_filters

class DonationFilter(MetadataFilterBase):
    donator = django_filters.CharFilter(method="filter_donator")
    created = ObjectTypeFilter(input_class=DateRangeInput, method="filter_created_range")
    updated = ObjectTypeFilter(input_class=DateRangeInput, method="filter_created_range")
    search = django_filters.CharFilter(method="filter_donation_search")
    channels = GlobalIDMultipleChoiceFilter(method="filter_channels")
    class Meta:
        model = Donation
        fields = ["donator", "created", "search"]

class DonationFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = DonationFilter
