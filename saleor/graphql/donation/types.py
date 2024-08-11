import graphene

from ...donation import models
from ...graphql.account.dataloaders import UserByUserCodeLoader
from ...graphql.account.utils import check_is_owner_or_has_one_of_perms
from ...graphql.core.doc_category import DOC_CATEGORY_DONATIONS
from ...graphql.utils import get_user_or_app_from_context
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import AccountPermissions, DonationPermissions
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.types import Money
from ..core.types.model import ModelObjectType


class Donation(ModelObjectType[models.Donation]):
    id = graphene.ID(required=True, description="The ID of the donation.")
    created_at = graphene.DateTime(
        required=False, description="The date and time when the donation was created."
    )
    updated_at = graphene.DateTime(
        required=False,
        description="The date and time when the donation was last updated.",
    )
    barcode = graphene.String(required=False, description="Barcode of the donation.")
    number = graphene.String(required=False, description="The number of the donation.")
    title = graphene.String(required=False, description="The title of the donation.")
    donator = graphene.Field(
        "saleor.graphql.account.types.User",
        description=f"The user who made the donation. Requires one of permissions: {AccountPermissions.MANAGE_USERS.name}, {DonationPermissions.MANAGE_DONATIONS.name}, f{AuthorizationFilters.OWNER.name}",
    )
    description = graphene.String(
        required=False, description="The description of the donation."
    )
    price = graphene.Field(
        Money, required=False, description="The price of the donation."
    )
    quantity = graphene.Int(required=False, description="The quantity of the donation.")
    status = graphene.String(required=False, description="The status of the donation")

    class Meta:
        description = "Represents donation."
        interfaces = [graphene.relay.Node]
        model = models.Donation

    @staticmethod
    def resolve_id(root: models.Donation, _info: ResolveInfo):
        return graphene.Node.to_global_id("Donation", root.pk)

    @staticmethod
    def resolve_number(root: models.Donation, _info: ResolveInfo):
        if not root.created_at or not root.number:
            return None
        return root.created_at.strftime("%y%m") + str(root.number).zfill(4)

    @staticmethod
    def resolve_title(root: models.Donation, _info: ResolveInfo):
        return root.title

    @staticmethod
    def resolve_description(root: models.Donation, _info: ResolveInfo):
        return root.description

    @staticmethod
    def resolve_created_at(root: models.Donation, _info: ResolveInfo):
        return root.created_at

    @staticmethod
    def resolve_updated_at(root: models.Donation, _info: ResolveInfo):
        return root.updated_at

    @staticmethod
    def resolve_price(root: models.Donation, _info: ResolveInfo):
        return root.price

    @staticmethod
    def resolve_quantity(root: models.Donation, _info: ResolveInfo):
        return root.quantity

    @staticmethod
    def resolve_donator(root: models.Donation, info: ResolveInfo):
        if not root.donator:
            return None
        requestor = get_user_or_app_from_context(info.context)
        donator = UserByUserCodeLoader(info.context).load(root.donator).get()
        check_is_owner_or_has_one_of_perms(
            requestor,
            donator,
            AccountPermissions.MANAGE_USERS,
            DonationPermissions.MANAGE_DONATIONS,
        )
        return donator

    @staticmethod
    def resolve_status(root: models.Donation, _info: ResolveInfo):
        return root.status


class DonationCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS
        node = Donation
