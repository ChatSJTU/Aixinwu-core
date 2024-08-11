import graphene
from django.utils import timezone

from ....donation import DonationStatus, models
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ...core.mutations import ModelMutation
from ...core.types.base import BaseInputObjectType
from ...core.types.common import DonationError
from ...core.utils import WebhookEventInfo
from ...donation.mutations.utils import (
    validate_donation_barcode,
    validate_donation_price,
    validate_donation_quantity,
    validate_donator,
    validate_update_permission,
)
from ...payment.mutations.payment.payment_check_balance import MoneyInput
from ..types import Donation


class DonationUpdateInput(BaseInputObjectType):
    title = graphene.String(required=False, description="The title of the donation.")
    description = graphene.String(
        required=False, description="The description of the donation."
    )
    quantity = graphene.Int(required=False, description="The quantity of the donation.")
    price = MoneyInput(required=False, description="The price of the donation.")
    barcode = graphene.String(
        required=False, description="The barcode of the donation."
    )
    donator = graphene.String(
        required=False, description="The Student ID of the donation"
    )

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS


class DonationUpdate(ModelMutation):
    donation = graphene.Field(
        Donation, description="The donation created by this mutation."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the donation.")
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
    def validate_donation_input(
        cls, info: ResolveInfo, instance: models.Donation, input
    ):
        if input.get("price", None):
            validate_donation_price(input)

        if input.get("quantity", None):
            validate_donation_quantity(input)

        if input.get("barcode", None):
            validate_donation_barcode(info, instance, input)

        if input.get("donator", None):
            validate_donator(info, input)

        validate_update_permission(info, instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, input):
        cls.validate_donation_input(info, instance, input)
        if input.get("price", None):
            input["currency"] = input["price"].currency
            input["price_amount"] = input["price"].amount
        input = super().clean_input(info, instance, input)
        input["status"] = DonationStatus.UNREVIEWED
        input["updated_at"] = timezone.now()
        return input
