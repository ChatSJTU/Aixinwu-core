from saleor.core.exceptions import PermissionDenied
from saleor.graphql.donation.dataloaders import DonationByIdDataLoader

from ...donation.models import Certificate, Donation
from ...permission.enums import DonationPermissions
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context


def resolve_donations(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    qs = Donation.objects.using(get_database_connection_name(info.context))
    if not user:
        raise PermissionDenied(
            message="You do not have access to Donations.",
        )
    if not user.has_perm(DonationPermissions.ADD_DONATIONS):
        return qs.filter(donator=user.code)
    return qs


def resolve_donation_by_id(info: ResolveInfo, id: str) -> Donation:
    _, id = from_global_id_or_error(id, "Donation")
    user = get_user_or_app_from_context(info.context)
    if not user:
        raise PermissionDenied(
            message="You do not have access to this donation.",
        )

    donation = DonationByIdDataLoader(info.context).load(id).get()

    if user.code == donation.donator or user.has_perm(
        DonationPermissions.ADD_DONATIONS
    ):
        return donation
    else:
        raise PermissionDenied(
            message="You do not have access to this donation.",
        )


def resolve_certificates(info: ResolveInfo):
    user = get_user_or_app_from_context(info.context)
    qs = Certificate.objects.using(get_database_connection_name(info.context))
    if not user or not user.has_perm(DonationPermissions.ADD_DONATIONS):
        raise PermissionDenied(message="You do not have access to Certificates.")
    return qs
