import graphene

from saleor.graphql.core.doc_category import DOC_CATEGORY_EVENTS


from .resolvers import resolve_balances
from .types import BalanceEventCountableConnection
from .filters import BalanceEventFilterInput
from .sorters import BalanceEventSortingInput
from ..core import ResolveInfo
from ..core.fields import FilterConnectionField
from ..core.connection import create_connection_slice, filter_connection_queryset


class EventQueries(graphene.ObjectType):
    balanceEvents = FilterConnectionField(
        BalanceEventCountableConnection,
        description="User Balance Events",
        filter=BalanceEventFilterInput(description="Filter the balance events"),
        sort_by=BalanceEventSortingInput(description="Sorting the balance events"),
        doc_category=DOC_CATEGORY_EVENTS,
    )

    @staticmethod
    def resolve_balanceEvents(_root, info: ResolveInfo, **kwargs):
        qs = resolve_balances(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(
            qs, info, kwargs, BalanceEventCountableConnection
        )
