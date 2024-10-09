import graphene

from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.fields import BaseField, FilterConnectionField
from ..donation.bulk_mutations.donation_bulk_complete import (
    DonationBulkComplete,
)
from .filters import DonationFilterInput
from .mutations import DonationComplete, DonationCreate, DonationDelete, DonationUpdate
from .resolvers import resolve_donation_by_id, resolve_donations
from .sorters import DonationSortingInput
from .types import Donation, DonationCountableConnection


class DonationQueries(graphene.ObjectType):
    donations = FilterConnectionField(
        DonationCountableConnection,
        description="Donations made by the user or collected by users if requested by staff.",
        sort_by=DonationSortingInput(description="Sort orders."),
        filter=DonationFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        doc_category=DOC_CATEGORY_ORDERS,
    )

    donation = BaseField(
        Donation,
        id=graphene.Argument(graphene.ID, description="ID of the donation"),
        doc_category=DOC_CATEGORY_ORDERS,
    )

    @staticmethod
    def resolve_donations(_root, info: ResolveInfo, **kwargs):
        qs = resolve_donations(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(qs, info, kwargs, DonationCountableConnection)

    @staticmethod
    def resolve_donation(_root, info: ResolveInfo, *, id):
        return resolve_donation_by_id(info, id=id)


class DonationMutations(graphene.ObjectType):
    donation_create = DonationCreate.Field()
    donation_update = DonationUpdate.Field()
    donation_delete = DonationDelete.Field()
    donation_complete = DonationComplete.Field()
    donation_bulk_complete = DonationBulkComplete.Field()
