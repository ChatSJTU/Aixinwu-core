from saleor.graphql.core.types.base import BaseInputObjectType
from saleor.graphql.donation.mutations.utils import (
    validate_complete_permission,
    validate_donation_price,
    validate_donation_quantity,
)
from saleor.graphql.donation.resolvers import resolve_donation_by_id
from saleor.permission.enums import DonationPermissions
from ...core.types.common import DonationError
from ...core.utils import WebhookEventInfo
from ....webhook.event_types import WebhookEventAsyncType
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ..dataloaders import DonationByIdDataLoader
from ...core.mutations import ModelMutation
from ....donation import DonationStatus, models
from ....account.models import User
from ..types import Donation
from ...core import ResolveInfo
from django.utils import timezone
import graphene


class DonationCompleteInput(BaseInputObjectType):
    accepted = graphene.Boolean(
        required=True, description="Whether this donation is accepted or not."
    )

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS


class DonationComplete(ModelMutation):
    donation = graphene.Field(Donation, description="The donation has been completed.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the donation.")
        input = DonationCompleteInput(
            required=True, description="The input required to complete a donation."
        )

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
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, input):
        validate_complete_permission(info, instance)
        input = super().clean_input(info, instance, input)
        if input["accepted"]:
            input["status"] = DonationStatus.COMPLETED
        else:
            input["status"] = DonationStatus.REJECTED
        input["updated_at"] = timezone.now()
        return input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        if instance.status == DonationStatus.COMPLETED and instance.donator:
            try:
                user = User.objects.get(code=instance.donator)
                user.balance += instance.price_amount
                user.save(update_fields=["balance"])
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
