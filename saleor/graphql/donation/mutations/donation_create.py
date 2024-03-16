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
    def validate_donation_input(cls, info: ResolveInfo, input):
        validate_donation_price(input)
        validate_donation_quantity(input)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, data):
        cls.validate_donation_input(info, data)
        data["currency"] = data["price"].currency
        data["price_amount"] = data["price"].amount
        return data

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        data["input"]["donator"] = info.context.user
        response = super().perform_mutation(_root, info, **data)
        return response
