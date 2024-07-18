from ..core.doc_category import DOC_CATEGORY_BARCODES
from ..core.types import BaseEnum
from ..core.types.sort_input import SortInputObjectType


class BarcodeSortField(BaseEnum):
    CREATION_DATE = ["created_at", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_BARCODES

    @property
    def description(self):
        if self.name in BarcodeSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort donations by {sort_name}."

        raise ValueError(f"Unsupported enum value: {self.value}")


class BarcodeSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_BARCODES
        sort_enum = BarcodeSortField
        type_name = "barcodes"
