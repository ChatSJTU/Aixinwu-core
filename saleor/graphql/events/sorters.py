from ..core.types.sort_input import SortInputObjectType
from ..core.doc_category import DOC_CATEGORY_EVENTS
from ..core.types import BaseEnum


class EventSortField(BaseEnum):
    CREATION_DATE = ["date", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_EVENTS

    @property
    def description(self):
        if self.name in EventSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort checkouts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class BalanceEventSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        sort_enum = EventSortField
        type_name = "balances"


class OrderEventSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        sort_enum = EventSortField
        type_name = "orders"


class CustomerEventSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        sort_enum = EventSortField
        type_name = "customers"
