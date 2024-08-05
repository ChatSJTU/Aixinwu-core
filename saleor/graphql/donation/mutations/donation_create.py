from saleor.permission.enums import DonationPermissions
from ...core import ResolveInfo
from ...core.utils import WebhookEventInfo
from ....webhook.event_types import WebhookEventAsyncType
from ...core.types.common import DonationError
from ...core.types.money import Money
from ....donation import models
from ..types import Donation
from ...core.types.base import BaseInputObjectType
from ...core.scalars import PositiveDecimal
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ...core.mutations import ModelMutation
from ...payment.mutations.payment.payment_check_balance import MoneyInput

from .utils import (
    validate_create_permission,
    validate_donation_barcode,
    validate_donation_price,
    validate_donation_quantity,
)

import graphene
import logging

logger = logging.getLogger()


class DonationCreateInput(BaseInputObjectType):
    title = graphene.String(required=True, description="The title of the donation.")
    description = graphene.String(
        required=True, description="The description of the donation."
    )
    quantity = graphene.Int(required=True, description="The quantity of the donation.")
    price = graphene.Field(
        MoneyInput, description="The price of the donation.", required=True
    )
    name = graphene.String(description="The name of the donator", required=True)
    donator = graphene.String(
        description="Student ID of the donator",
        required=False,
    )
    barcode = graphene.String(required=True, description="The barcode of the donation.")

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS


class DonationCreate(ModelMutation):
    class Arguments:
        input = DonationCreateInput(
            required=True,
            description="Fields required to create a donation.",
        )

    class Meta:
        description = "Create a new donation."
        doc_category = DOC_CATEGORY_DONATIONS
        model = models.Donation
        object_type = Donation
        return_field_name = "donation"
        error_type_class = DonationError
        error_type_fields = "donation_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.DONATION_CREATED,
                description="A donation has been created.",
            )
        ]

    @classmethod
    def validate_creation_input(
        cls, info: ResolveInfo, instance: models.Donation, input
    ):
        validate_donation_price(input)
        validate_donation_quantity(input)
        validate_donation_barcode(info, input)
        validate_create_permission(info, instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, input):
        cls.validate_creation_input(info, instance, input)
        input = super().clean_input(info, instance, input)
        input["currency"] = input["price"].currency
        input["price_amount"] = input["price"].amount
        return input
