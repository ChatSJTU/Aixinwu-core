import graphene

from .mutations import *
from saleor.permission.enums import DonationPermissions

from ...graphql.donation.filters import DonationFilter
from ...graphql.core.doc_category import DOC_CATEGORY_ORDERS
from ...graphql.core.types.filter_input import FilterInputObjectType
from .filters import DonationFilterInput
from .sorters import DonationSortingInput
from ..core.fields import BaseField, FilterConnectionField
from .types import Donation, DonationCountableConnection
from ..core import ResolveInfo
from .resolvers import resolve_donation_by_id, resolve_donations


class DonationQueries(graphene.ObjectType):
    donations = FilterConnectionField(
        DonationCountableConnection,
        description="Donations made by the user or collected by users if requested by staff.",
        sort_by=DonationSortingInput(description="Sort orders."),
        filter=DonationFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        permissions=[DonationPermissions.MANAGE_DONATIONS],
        doc_category=DOC_CATEGORY_ORDERS,
    )

    def resolve_donations(_root, info: ResolveInfo, *, token=None, id=None):
        return resolve_donations(info)


class DonationMutations(graphene.ObjectType):
    donation_create = DonationCreate.Field()
    donation_update = DonationUpdate.Field()
    donation_delete = DonationDelete.Field()
    donation_complete = DonationComplete.Field()
