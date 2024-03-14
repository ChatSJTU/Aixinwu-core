from uuid import UUID
from saleor.graphql.core import ResolveInfo
from saleor.graphql.core.context import get_database_connection_name
from ...donation.models import Donation


def resolve_donations(info: ResolveInfo) -> list[Donation]:
    if info.context.user.is_staff:
        return list(
            Donation.objects.using(get_database_connection_name(info.context)).all()
        )

    return list(
        Donation.objects.using(get_database_connection_name(info.context))
        .filter(user=info.context.user)
        .all()
    )


def resolve_donation_by_id(info: ResolveInfo, id: UUID) -> Donation:
    return Donation.objects.using(get_database_connection_name(info.context)).get(
        id=id, donator_id=info.context.user.id
    )
