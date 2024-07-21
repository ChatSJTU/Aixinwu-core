from uuid import UUID

import graphene

from saleor.core.exceptions import PermissionDenied
from saleor.graphql.account.utils import is_owner_or_has_one_of_perms
from saleor.graphql.donation.dataloaders import DonationByIdDataLoader
from saleor.graphql.payment.utils import check_if_requestor_has_access
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context
from ...donation.models import Donation
from ...permission.enums import DonationPermissions
from ..core.utils import from_global_id_or_error


def resolve_donations(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    qs = Donation.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(
            message=f"You do not have access to Donations.",
        )
    if not user.has_perm(DonationPermissions.MANAGE_DONATIONS):
        return qs.filter(donator=user.code)
    return qs


def resolve_donation_by_id(info: ResolveInfo, id: str) -> Donation:
    _, id = from_global_id_or_error(id, "Donation")
    user = get_user_or_app_from_context(info.context)
    if not user:
        raise PermissionDenied(
            message=f"You do not have access to this donation.",
        )

    donation = DonationByIdDataLoader(info.context).load(id).get()

    if user.code == donation.donator or user.has_perm(
        DonationPermissions.MANAGE_DONATIONS
    ):
        return donation
    else:
        raise PermissionDenied(
            message=f"You do not have access to this donation.",
        )
