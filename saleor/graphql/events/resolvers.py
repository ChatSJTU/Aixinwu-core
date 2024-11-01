from typing import cast

from saleor.product.models import ProductEvent, ProductVariantEvent

from ...account.models import BalanceEvent, CustomerEvent, User
from ...core.exceptions import PermissionDenied
from ...order.models import OrderEvent
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context


def resolve_balance_events(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = BalanceEvent.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(message=f"You do not have access to Balance Events.")
    if user.is_superuser or user.is_staff:
        return qs
    return qs.filter(user=user)


def resolve_order_events(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = OrderEvent.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(message=f"You do not have access to Order Events.")

    if user.is_superuser or user.is_staff:
        return qs

    return qs.filter(user=user)


def resolve_customer_events(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = CustomerEvent.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(message=f"You do not have access to Customer Events.")

    if user.is_superuser or user.is_staff:
        return qs

    return qs.filter(user=user)

def resolve_product_events(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = ProductEvent.objects.using(get_database_connection_name(info.context))
    if not user or not (user.is_superuser or user.is_staff):
        raise PermissionDenied(message=f"You do not have access to Product Events.")

    return qs

def resolve_product_variant_events(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = ProductVariantEvent.objects.using(get_database_connection_name(info.context))
    if not user or not (user.is_superuser or user.is_staff):
        raise PermissionDenied(message=f"You do not have access to ProductVariant Events.")

    return qs
