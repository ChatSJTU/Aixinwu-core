from decimal import DecimalException
import graphene
from saleor.graphql.account.utils import check_is_owner_or_has_one_of_perms

from saleor.graphql.utils import get_user_or_app_from_context

from ...graphql.account.dataloaders import UserByUserIdLoader
from ...permission.auth_filters import AuthorizationFilters
from ...graphql.core.doc_category import DOC_CATEGORY_DONATIONS
from ...permission.enums import AccountPermissions, DonationPermissions
from ..core.connection import CountableConnection
from ..core.types.model import ModelObjectType
from ..core.types import Money
from ..core import ResolveInfo
from ...donation import models


class Donation(ModelObjectType[models.Donation]):
    id = graphene.ID(required=True, description="The ID of the donation.")
    created_at = graphene.DateTime(
        required=True, description="The date and time when the donation was created."
    )
    updated_at = graphene.DateTime(
        required=True,
        description="The date and time when the donation was last updated.",
    )
    completed = graphene.Boolean(
        required=False,
        description="Whether this donation is completed or not.",
    )
    title = graphene.String(required=True, description="The title of the donation.")
    donator = graphene.Field(
        "saleor.graphql.account.types.User",
        description=f"The user who made the donation. Requires one of permissions: {AccountPermissions.MANAGE_USERS.name}, {DonationPermissions.MANAGE_DONATIONS.name}, f{AuthorizationFilters.OWNER.name}",
    )
    description = graphene.String(
        required=True, description="The description of the donation."
    )
    price = graphene.Field(
        Money, required=True, description="The price of the donation."
    )
    quantity = graphene.Int(required=True, description="The quantity of the donation.")

    class Meta:
        description = "Represents donation."
        interfaces = [graphene.relay.Node]
        model = models.Donation

    @staticmethod
    def resolve_id(root: models.Donation, _info: ResolveInfo):
        return graphene.Node.to_global_id("Donation", root.pk)

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
    def resolve_user(root: models.Donation, info: ResolveInfo):
        if not root.user_id:
            return None
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor,
            root.user,
            AccountPermissions.MANAGE_USERS,
            DonationPermissions.MANAGE_DONATIONS,
        )
        return root.user

    @staticmethod
    def resolve_completed(root: models.Donation, _info: ResolveInfo):
        return root.completed


class DonationCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS
        node = Donation
