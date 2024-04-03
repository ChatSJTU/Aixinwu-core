from uuid import UUID

import graphene

from saleor.graphql.donation.dataloaders import DonationByIdDataLoader
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context
from ...donation.models import Donation
from ...permission.enums import DonationPermissions
from ..core.utils import from_global_id_or_error


def resolve_donations(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    qs = Donation.objects.using(get_database_connection_name(info.context)).filter(
        deleted_at__isnull=True
    )

    if user.has_perm(DonationPermissions.MANAGE_DONATIONS):
        return qs

    return qs.filter(donator=user)


def resolve_donation_by_id(info: ResolveInfo, id: str) -> Donation:
    _, local_id = from_global_id_or_error(id, "Donation")

    return DonationByIdDataLoader(info.context).load(local_id).get()
