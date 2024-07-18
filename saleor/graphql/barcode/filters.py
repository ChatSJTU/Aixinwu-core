from ...barcode.models import Barcode
from ..core.doc_category import DOC_CATEGORY_BARCODES
from ..core.filters import MetadataFilterBase, ObjectTypeFilter
from ..core.types.common import IntRangeInput
from ..core.types.filter_input import FilterInputObjectType
from ..utils.filters import filter_range_field


def filter_year_month_at_range(qs, _, value):
    return filter_range_field(qs, "year_month", value)


class BarcodeFilter(MetadataFilterBase):
    year_month = ObjectTypeFilter(
        input_class=IntRangeInput,
        method=filter_year_month_at_range,
    )

    class Meta:
        model = Barcode
        fields = ["year_month"]


class BarcodeFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_BARCODES
        filterset_class = BarcodeFilter
