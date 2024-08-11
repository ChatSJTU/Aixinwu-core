import graphene

from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.doc_category import DOC_CATEGORY_EVENTS
from ..core.fields import FilterConnectionField
from ..order.types import OrderEventCountableConnection
from .filters import (
    BalanceEventFilterInput,
    CustomerEventFilterInput,
    OrderEventFilterInput,
)
from .resolvers import (
    resolve_balance_events,
    resolve_customer_events,
    resolve_order_events,
)
from .sorters import (
    BalanceEventSortingInput,
    CustomerEventSortingInput,
    OrderEventSortingInput,
)
from .types import (
    BalanceEventCountableConnection,
    CustomerEventCountableConnection,
)


class EventQueries(graphene.ObjectType):
    balanceEvents = FilterConnectionField(
        BalanceEventCountableConnection,
        description="User Balance Events",
        filter=BalanceEventFilterInput(description="Filter the balance events"),
        sort_by=BalanceEventSortingInput(description="Sorting the balance events"),
        doc_category=DOC_CATEGORY_EVENTS,
    )

    orderEvents = FilterConnectionField(
        OrderEventCountableConnection,
        description="Order Events",
        filter=OrderEventFilterInput(description="Filter the order events"),
        sort_by=OrderEventSortingInput(description="Sorting the order events"),
        doc_category=DOC_CATEGORY_EVENTS,
    )

    customerEvents = FilterConnectionField(
        CustomerEventCountableConnection,
        description="Customer Events",
        filter=CustomerEventFilterInput(description="Filter the customer events"),
        sort_by=CustomerEventSortingInput(description="Sorting the customer events"),
        doc_category=DOC_CATEGORY_EVENTS,
    )

    @staticmethod
    def resolve_balanceEvents(_root, info: ResolveInfo, **kwargs):
        qs = resolve_balance_events(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(
            qs, info, kwargs, BalanceEventCountableConnection
        )

    @staticmethod
    def resolve_orderEvents(_root, info: ResolveInfo, **kwargs):
        qs = resolve_order_events(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(
            qs, info, kwargs, BalanceEventCountableConnection
        )

    @staticmethod
    def resolve_customerEvents(_root, info: ResolveInfo, **kwargs):
        qs = resolve_customer_events(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(
            qs, info, kwargs, BalanceEventCountableConnection
        )
