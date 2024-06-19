from typing import cast

from saleor.core.exceptions import PermissionDenied
from ...account.models import BalanceEvent, User
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context


def resolve_balances(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    user = cast(User, user)
    qs = BalanceEvent.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(message=f"You do not have access to Balance Events.")
    if user.is_superuser:
        return qs
    return qs.filter(user=user)
