from saleor.permission.enums import DonationPermissions
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


class DonationComplete(ModelMutation):
    success = graphene.Boolean(description="The donation has been completed.")

    class Arguments:
        id = graphene.ID(description="ID of the donation to complete.", required=True)

    class Meta:
        description = "Complete a new donation."
        doc_category = DOC_CATEGORY_DONATIONS
        model = models.Donation
        object_type = Donation
        return_field_name = "donation"
        error_type_class = DonationError
        error_type_fields = "donation_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.DONATION_COMPLETED,
                description="A donation has been created.",
            )
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_donation_input(info, instance)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):
        donation = DonationByIdDataLoader(info.context).load(input["id"])
        if not donation:
            return cls(errors=[DonationError(code="NOT_FOUND")], success=False)
        if donation.donator != info.context.user or not info.context.user.has_perm(
            DonationPermissions.MANAGE_DONATIONS
        ):
            return cls(errors=[DonationError(code="PERMISSION_DENIED")], success=False)
        donation.completed = True
        donation.save(update_fields=["completed"])
        return cls(errors=[], success=True)
