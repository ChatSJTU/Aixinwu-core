from ..core.types.sort_input import SortInputObjectType
from ..core.doc_category import DOC_CATEGORY_DONATIONS
from ..core.types import BaseEnum


class DonationSortField(BaseEnum):
    CREATION_DATE = ["created_at", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS

    @property
    def description(self):
        if self.name in DonationSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort checkouts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class DonationSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS
        sort_enum = DonationSortField
        type_name = "donations"
