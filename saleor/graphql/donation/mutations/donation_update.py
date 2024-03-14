from ...core.scalars import PositiveDecimal
from ...core.types.base import BaseInputObjectType
from ....permission.enums import DonationPermissions
from ...core.types.common import DonationError
from ...core.utils import WebhookEventInfo
from ....webhook.event_types import WebhookEventAsyncType
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ..dataloaders import DonationByIdDataLoader
from ...core.mutations import ModelMutation
from ....donation import models
from ..types import Donation
from ...core import ResolveInfo
import graphene


class DonationUpdateInput(BaseInputObjectType):
    id = graphene.ID(required=True, description="ID of the donation.")
    title = graphene.String(required=False, description="The title of the donation.")
    description = graphene.String(
        required=False, description="The description of the donation."
    )
    quantity = graphene.Int(required=False, description="The quantity of the donation.")
    price = PositiveDecimal(required=False, description="The price of the donation.")

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS


class DonationUpdate(ModelMutation):
    success = graphene.Boolean(description="The donation has been updated.")

    class Arguments:
        input = DonationUpdateInput(
            required=True, description="Fields required to update a donation."
        )

    class Meta:
        description = "Update a new donation."
        doc_category = DOC_CATEGORY_DONATIONS
        model = models.Donation
        object_type = Donation
        return_field_name = "donation"
        error_type_class = DonationError
        error_type_fields = "donation_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.DONATION_UPDATED,
                description="A donation has been updated.",
            )
        ]

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        input,
        /,
    ):
        donation = DonationByIdDataLoader(info.context).load(input["id"])
        if not donation:
            return cls(errors=[DonationError(code="NOT_FOUND")], success=False)
        if donation.donator != info.context.user or not info.context.user.has_perm(
            DonationPermissions.MANAGE_DONATIONS
        ):
            return cls(errors=[DonationError(code="PERMISSION_DENIED")], success=False)
        super().perform_mutation(_root, info, **input)
